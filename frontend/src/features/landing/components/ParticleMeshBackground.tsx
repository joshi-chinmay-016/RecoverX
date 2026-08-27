import React, { useEffect, useRef } from 'react';

interface Particle {
  x: number;
  y: number;
  z: number;
  vx: number;
  vy: number;
  vz: number;
  size: number;
  color: string;
  alpha: number;
}

export const ParticleMeshBackground: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const mouseRef = useRef<{ x: number; y: number; targetX: number; targetY: number }>({
    x: 0,
    y: 0,
    targetX: 0,
    targetY: 0,
  });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    const handleMouseMove = (e: MouseEvent) => {
      mouseRef.current.targetX = (e.clientX - width / 2) * 0.05;
      mouseRef.current.targetY = (e.clientY - height / 2) * 0.05;
    };

    window.addEventListener('resize', handleResize);
    window.addEventListener('mousemove', handleMouseMove);

    // Particle Palette
    const colors = [
      'rgba(99, 102, 241,',   // Indigo
      'rgba(236, 72, 153,',   // Pink
      'rgba(16, 185, 129,',   // Emerald
      'rgba(56, 189, 248,',   // Sky
    ];

    const particleCount = Math.min(Math.floor((width * height) / 14000), 90);
    const particles: Particle[] = [];

    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: (Math.random() - 0.5) * width * 1.2,
        y: (Math.random() - 0.5) * height * 1.2,
        z: Math.random() * 800 + 200,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        vz: (Math.random() - 0.5) * 0.2,
        size: Math.random() * 2 + 1.2,
        color: colors[Math.floor(Math.random() * colors.length)],
        alpha: Math.random() * 0.5 + 0.2,
      });
    }

    const fov = 400;

    const render = () => {
      // Smooth mouse easing
      mouseRef.current.x += (mouseRef.current.targetX - mouseRef.current.x) * 0.05;
      mouseRef.current.y += (mouseRef.current.targetY - mouseRef.current.y) * 0.05;

      ctx.clearRect(0, 0, width, height);

      const cx = width / 2 + mouseRef.current.x;
      const cy = height / 2 + mouseRef.current.y;

      // Update and project particles
      const projected: { x: number; y: number; scale: number; p: Particle }[] = [];

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];

        p.x += p.vx;
        p.y += p.vy;
        p.z += p.vz;

        // Boundaries wrapping in 3D
        if (p.x < -width) p.x = width;
        if (p.x > width) p.x = -width;
        if (p.y < -height) p.y = height;
        if (p.y > height) p.y = -height;
        if (p.z < 100) p.z = 900;
        if (p.z > 1000) p.z = 150;

        const scale = fov / (fov + p.z);
        const px = p.x * scale + cx;
        const py = p.y * scale + cy;

        projected.push({ x: px, y: py, scale, p });
      }

      // Draw connections
      ctx.lineWidth = 0.6;
      for (let i = 0; i < projected.length; i++) {
        for (let j = i + 1; j < projected.length; j++) {
          const p1 = projected[i];
          const p2 = projected[j];

          const dx = p1.x - p2.x;
          const dy = p1.y - p2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 130) {
            const alpha = (1 - dist / 130) * 0.22 * Math.min(p1.p.alpha, p2.p.alpha);
            ctx.strokeStyle = `rgba(99, 102, 241, ${alpha})`;
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
          }
        }
      }

      // Draw particles with glowing radial gradient
      for (let i = 0; i < projected.length; i++) {
        const { x, y, scale, p } = projected[i];
        const r = p.size * scale * 1.5;

        if (r <= 0) continue;

        const grad = ctx.createRadialGradient(x, y, 0, x, y, r * 2.5);
        grad.addColorStop(0, `${p.color} ${p.alpha})`);
        grad.addColorStop(0.5, `${p.color} ${p.alpha * 0.4})`);
        grad.addColorStop(1, `${p.color} 0)`);

        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(x, y, r * 2, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = `${p.color} 0.9)`;
        ctx.beginPath();
        ctx.arc(x, y, Math.max(0.6, r * 0.6), 0, Math.PI * 2);
        ctx.fill();
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-0 opacity-70"
    />
  );
};
