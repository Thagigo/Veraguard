import { useEffect, useRef } from 'react';

interface WantedPosterProps {
    address: string;
    risk?: string;
    className?: string;
}

export default function WantedPoster({ address, risk = "UNKNOWN", className = "" }: WantedPosterProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    if (!address) return null;

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // Seeded Random Logic
        const seed = address.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
        const random = (offset: number) => {
            const x = Math.sin(seed + offset) * 10000;
            return x - Math.floor(x);
        };

        // Clear
        ctx.fillStyle = '#1a1a1a';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Draw "Crystallized" Pattern
        const segments = 8 + Math.floor(random(1) * 8); // 8-16 segments
        const cx = canvas.width / 2;
        const cy = canvas.height / 2;
        const radius = canvas.width * 0.4;

        ctx.strokeStyle = risk === "High" ? '#ef4444' : risk === "Medium" ? '#f59e0b' : '#10b981';
        ctx.lineWidth = 2;

        ctx.beginPath();
        for (let i = 0; i <= segments; i++) {
            const angle = (i / segments) * Math.PI * 2;
            const r = radius * (0.5 + random(i) * 0.5);
            const x = cx + Math.cos(angle) * r;
            const y = cy + Math.sin(angle) * r;

            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);

            // Inner lines
            ctx.moveTo(cx, cy);
            ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.stroke();

        // Overlay "Wanted" Text
        ctx.font = 'bold 20px Courier New';
        ctx.fillStyle = '#ffffff';
        ctx.textAlign = 'center';
        ctx.fillText('WANTED', cx, 30);

        ctx.font = '10px Courier New';
        ctx.fillStyle = '#aaaaaa';
        ctx.fillText(address.substring(0, 8) + '...', cx, canvas.height - 15);

    }, [address, risk]);

    return (
        <canvas
            ref={canvasRef}
            width={200}
            height={250}
            className={`rounded-lg border border-slate-700 shadow-2xl ${className}`}
        />
    );
}
