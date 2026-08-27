import React, { useState, useRef, MouseEvent, ReactNode } from 'react';

interface TiltCardProps {
  children: ReactNode;
  className?: string;
  maxRotation?: number; // max tilt in degrees
  glowColor?: string; // specular highlight color
  depth?: number; // translateZ for children
}

export const TiltCard: React.FC<TiltCardProps> = ({
  children,
  className = '',
  maxRotation = 12,
  glowColor = 'rgba(99, 102, 241, 0.25)',
  depth = 30,
}) => {
  const cardRef = useRef<HTMLDivElement | null>(null);
  const [rotateX, setRotateX] = useState(0);
  const [rotateY, setRotateY] = useState(0);
  const [glowPosition, setGlowPosition] = useState({ x: 50, y: 50, opacity: 0 });
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseMove = (e: MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const rotX = -((y - centerY) / centerY) * maxRotation;
    const rotY = ((x - centerX) / centerX) * maxRotation;

    setRotateX(rotX);
    setRotateY(rotY);

    const glowX = (x / rect.width) * 100;
    const glowY = (y / rect.height) * 100;
    setGlowPosition({ x: glowX, y: glowY, opacity: 1 });
  };

  const handleMouseEnter = () => {
    setIsHovered(true);
  };

  const handleMouseLeave = () => {
    setIsHovered(false);
    setRotateX(0);
    setRotateY(0);
    setGlowPosition((prev) => ({ ...prev, opacity: 0 }));
  };

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className={`relative perspective-1000 transform-gpu transition-transform duration-200 ease-out cursor-default ${className}`}
      style={{
        transform: `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) ${
          isHovered ? 'scale3d(1.02, 1.02, 1.02)' : 'scale3d(1, 1, 1)'
        }`,
      }}
    >
      {/* Specular highlight gradient */}
      <div
        className="absolute inset-0 rounded-[inherit] pointer-events-none transition-opacity duration-300 z-30"
        style={{
          opacity: glowPosition.opacity,
          background: `radial-gradient(circle 220px at ${glowPosition.x}% ${glowPosition.y}%, ${glowColor}, transparent 70%)`,
        }}
      />

      {/* 3D Elevated Content Layer */}
      <div
        className="relative z-10 w-full h-full transform-style-3d transition-transform duration-200"
        style={{
          transform: isHovered ? `translateZ(${depth}px)` : 'translateZ(0px)',
        }}
      >
        {children}
      </div>
    </div>
  );
};
