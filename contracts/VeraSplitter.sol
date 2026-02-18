// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title VeraSplitter
 * @dev Optimization of Finance Core: Automating the 60/25/15 split.
 */
contract VeraSplitter {

    // -------------------------------------------------------------------------
    //  Optimized Finance Core: Hardcoded Split Targets
    // -------------------------------------------------------------------------
    
    // 60% - Funding the Security Vault (Simulations, Heavy Compute)
    address public constant SECURITY_VAULT = 0x1111111111111111111111111111111111111111; 

    // 25% - Founder Yield (Sustaining Leadership)
    address public constant FOUNDER_YIELD  = 0x2222222222222222222222222222222222222222;

    // 15% - War Chest (Future Development, Rapid Response)
    address public constant WAR_CHEST      = 0x3333333333333333333333333333333333333333;

    // Events for transparency
    event PaymentSplit(address indexed payer, uint256 amount, uint256 timestamp);

    /**
     * @dev Receive function calls the split logic automatically.
     */
    receive() external payable {
        _splitFunds(msg.value);
    }

    /**
     * @dev Fallback function in case calldata is sent.
     */
    fallback() external payable {
        _splitFunds(msg.value);
    }

    /**
     * @dev Internal function to calculate and transfer the splits.
     * Uses minimal gas logic.
     */
    function _splitFunds(uint256 amount) internal {
        require(amount > 0, "No funds sent");

        uint256 vaultShare   = (amount * 60) / 100;
        uint256 founderShare = (amount * 25) / 100;
        // The rest goes to War Chest to handle rounding dust
        uint256 warChestShare = amount - vaultShare - founderShare;

        // Perform Transfers
        // Using call instead of transfer to avoid gas limits on multisigs/safes
        (bool s1, ) = payable(SECURITY_VAULT).call{value: vaultShare}("");
        (bool s2, ) = payable(FOUNDER_YIELD).call{value: founderShare}("");
        (bool s3, ) = payable(WAR_CHEST).call{value: warChestShare}("");
        
        // We do not revert if one fails to ensure partial settlement? 
        // No, strict atomic settlement is better for finance core.
        require(s1 && s2 && s3, "Transfer failed");

        emit PaymentSplit(msg.sender, amount, block.timestamp);
    }
}
