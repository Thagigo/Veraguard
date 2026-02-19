// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title VeraAnchor
 * @dev Service-Level Verification & Restitution Logic.
 *      Anchors semantic proofs of audits to the chain.
 *      Enforces the "24-Hour" Guarantee.
 */
contract VeraAnchor {

    struct AuditRequest {
        address requester;
        uint256 amountPaid;
        uint256 timestamp;
        bool fulfilled;
        string reportHash;
    }

    // Mapping from Request ID (or TX Hash) to Request Data
    mapping(bytes32 => AuditRequest) public requests;

    // Events
    event AuditRequested(bytes32 indexed requestId, address indexed requester, uint256 amount);
    event AuditAnchored(bytes32 indexed requestId, string reportHash, uint256 timestamp);
    event RestitutionClaimed(bytes32 indexed requestId, address indexed requester, uint256 amount);

    // Modifier
    modifier onlyOpen(bytes32 requestId) {
        require(requests[requestId].timestamp > 0, "Request not found");
        require(!requests[requestId].fulfilled, "Request already fulfilled");
        _;
    }

    /**
     * @dev Called by the Payment Handler (or Splitter) to register a new job.
     *      In a real system, this accepts ETH/Credits. Here we simulate the logic.
     */
    function registerAuditRequest(bytes32 requestId, address user) external payable {
        requests[requestId] = AuditRequest({
            requester: user,
            amountPaid: msg.value,
            timestamp: block.timestamp,
            fulfilled: false,
            reportHash: ""
        });

        emit AuditRequested(requestId, user, msg.value);
    }

    /**
     * @dev Called by the VeraGuard Backend (Oracle) to anchor the proof.
     *      This fulfills the Service-Level Agreement (SLA).
     */
    function completeAudit(bytes32 requestId, string calldata ipfsHash) external onlyOpen(requestId) {
        // In prod: require(msg.sender == ORACLE_KEY);
        
        requests[requestId].fulfilled = true;
        requests[requestId].reportHash = ipfsHash;
        
        emit AuditAnchored(requestId, ipfsHash, block.timestamp);
    }

    /**
     * @dev The "Kill Switch" for users.
     *      If 24 hours pass without an anchor, the user can claw back their funds.
     */
    function claimRestitution(bytes32 requestId) external onlyOpen(requestId) {
        require(msg.sender == requests[requestId].requester, "Not original requester");
        require(block.timestamp > requests[requestId].timestamp + 24 hours, "SLA buffer active (24h)");

        // Mark as fulfilled (by restitution) to prevent double claim
        requests[requestId].fulfilled = true;
        requests[requestId].reportHash = "RESTITUTION_CLAIMED";

        uint256 refund = requests[requestId].amountPaid;
        
        (bool success, ) = payable(msg.sender).call{value: refund}("");
        require(success, "Refund transfer failed");

        emit RestitutionClaimed(requestId, msg.sender, refund);
    }
}
