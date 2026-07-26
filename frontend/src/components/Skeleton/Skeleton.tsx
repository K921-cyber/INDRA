import React from 'react';
import { motion, type Variants } from 'framer-motion';

type SkeletonVariant = 'card' | 'text' | 'avatar' | 'chart' | 'map' | 'inline';

interface SkeletonProps {
  variant?: SkeletonVariant;
  width?: string | number;
  height?: string | number;
  count?: number;
  style?: React.CSSProperties;
  className?: string;
}

const shimmer: Variants = {
  initial: { backgroundPosition: '-200% 0' },
  animate: {
    backgroundPosition: '200% 0',
    transition: {
      repeat: Infinity,
      duration: 1.5,
      ease: 'easeInOut',
    },
  },
};

export function SkeletonCard({ style, className }: { style?: React.CSSProperties; className?: string }) {
  return (
    <motion.div
      className={`skeleton-card ${className || ''}`}
      style={{
        background: 'linear-gradient(90deg, rgba(30,42,64,0.4) 0%, rgba(50,65,90,0.2) 50%, rgba(30,42,64,0.4) 100%)',
        backgroundSize: '200% 100%',
        borderRadius: 8,
        padding: 16,
        ...style,
      }}
      variants={shimmer}
      initial="initial"
      animate="animate"
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
        <div style={{
          width: 32, height: 32, borderRadius: 8,
          background: 'rgba(50,65,90,0.3)',
        }} />
        <div style={{ flex: 1 }}>
          <div style={{
            width: '60%', height: 10, borderRadius: 4,
            background: 'rgba(50,65,90,0.3)', marginBottom: 6,
          }} />
          <div style={{
            width: '40%', height: 8, borderRadius: 4,
            background: 'rgba(50,65,90,0.2)',
          }} />
        </div>
      </div>
      <div style={{
        width: '100%', height: 6, borderRadius: 3,
        background: 'rgba(50,65,90,0.2)', marginBottom: 8,
      }} />
      <div style={{
        width: '80%', height: 6, borderRadius: 3,
        background: 'rgba(50,65,90,0.15)',
      }} />
    </motion.div>
  );
}

export function SkeletonText({ lines = 3, width }: { lines?: number; width?: string }) {
  return (
    <motion.div
      style={{
        background: 'linear-gradient(90deg, rgba(30,42,64,0.3) 0%, rgba(50,65,90,0.15) 50%, rgba(30,42,64,0.3) 100%)',
        backgroundSize: '200% 100%',
        borderRadius: 4,
        width: width || '100%',
      }}
      variants={shimmer}
      initial="initial"
      animate="animate"
    >
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          style={{
            height: 8,
            width: `${100 - i * 15}%`,
            borderRadius: 4,
            background: 'rgba(50,65,90,0.25)',
            marginBottom: i < lines - 1 ? 8 : 0,
          }}
        />
      ))}
    </motion.div>
  );
}

export function SkeletonAvatar({ size = 40 }: { size?: number }) {
  return (
    <motion.div
      style={{
        width: size,
        height: size,
        borderRadius: '50%',
        background: 'linear-gradient(90deg, rgba(30,42,64,0.4) 0%, rgba(50,65,90,0.2) 50%, rgba(30,42,64,0.4) 100%)',
        backgroundSize: '200% 100%',
        flexShrink: 0,
      }}
      variants={shimmer}
      initial="initial"
      animate="animate"
    />
  );
}

export function SkeletonChart({ height = 100 }: { height?: number }) {
  return (
    <motion.div
      style={{
        width: '100%',
        height,
        borderRadius: 8,
        background: 'linear-gradient(90deg, rgba(30,42,64,0.3) 0%, rgba(50,65,90,0.15) 50%, rgba(30,42,64,0.3) 100%)',
        backgroundSize: '200% 100%',
        display: 'flex',
        alignItems: 'flex-end',
        gap: 4,
        padding: '12px 8px',
      }}
      variants={shimmer}
      initial="initial"
      animate="animate"
    >
      {[35, 60, 45, 80, 55, 70, 40].map((h, i) => (
        <div
          key={i}
          style={{
            flex: 1,
            height: `${h}%`,
            borderRadius: '4px 4px 0 0',
            background: 'rgba(50,65,90,0.3)',
          }}
        />
      ))}
    </motion.div>
  );
}

export function SkeletonMap() {
  return (
    <motion.div
      style={{
        width: '100%',
        height: '100%',
        borderRadius: 8,
        background: 'linear-gradient(90deg, rgba(8,12,24,0.9) 0%, rgba(16,24,40,0.8) 50%, rgba(8,12,24,0.9) 100%)',
        backgroundSize: '200% 100%',
        position: 'relative',
        overflow: 'hidden',
      }}
      variants={shimmer}
      initial="initial"
      animate="animate"
    >
      {/* Grid pattern */}
      <div style={{
        position: 'absolute', inset: 0,
        backgroundImage: 'linear-gradient(rgba(59,130,246,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(59,130,246,0.04) 1px, transparent 1px)',
        backgroundSize: '40px 40px',
      }} />
      {/* Decorative circles */}
      {[
        { top: '20%', left: '30%', size: 60 },
        { top: '50%', left: '60%', size: 80 },
        { top: '70%', left: '40%', size: 50 },
        { top: '35%', left: '70%', size: 40 },
      ].map((c, i) => (
        <div key={i} style={{
          position: 'absolute',
          top: c.top, left: c.left,
          width: c.size, height: c.size,
          borderRadius: '50%',
          background: 'rgba(59,130,246,0.06)',
          border: '1px solid rgba(59,130,246,0.08)',
          transform: 'translate(-50%, -50%)',
        }} />
      ))}
    </motion.div>
  );
}

export function SkeletonInline({ width = 120 }: { width?: number }) {
  return (
    <motion.div
      style={{
        display: 'inline-block',
        width,
        height: 10,
        borderRadius: 4,
        background: 'linear-gradient(90deg, rgba(30,42,64,0.3) 0%, rgba(50,65,90,0.15) 50%, rgba(30,42,64,0.3) 100%)',
        backgroundSize: '200% 100%',
        verticalAlign: 'middle',
      }}
      variants={shimmer}
      initial="initial"
      animate="animate"
    />
  );
}

export default function Skeleton({
  variant = 'text',
  width,
  height,
  count = 1,
  style,
  className,
}: SkeletonProps) {
  const items = Array.from({ length: count });

  return (
    <>
      {items.map((_, i) => {
        switch (variant) {
          case 'card':
            return <SkeletonCard key={i} style={{ ...style, width, height }} className={className} />;
          case 'avatar':
            return <SkeletonAvatar key={i} size={typeof width === 'number' ? width : 40} />;
          case 'chart':
            return <SkeletonChart key={i} height={typeof height === 'number' ? height : 100} />;
          case 'map':
            return <SkeletonMap key={i} />;
          case 'inline':
            return <SkeletonInline key={i} width={typeof width === 'number' ? width : 120} />;
          case 'text':
          default:
            return <SkeletonText key={i} lines={3} width={typeof width === 'string' ? width : undefined} />;
        }
      })}
    </>
  );
}
