/**
 * Optimized Image Component with Lazy Loading and Progressive Enhancement
 * Requirements: 12.3, 8.9
 *
 * This component provides intelligent image loading with:
 * - Lazy loading with intersection observer
 * - Progressive enhancement with blur placeholder
 * - Responsive images for different screen densities
 * - Error handling and fallback images
 * - Performance monitoring
 */

'use client';

import Image from 'next/image';
import { useState, useRef, useEffect } from 'react';
import { cn } from '@/lib/utils';

interface OptimizedImageProps {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  className?: string;
  priority?: boolean;
  fill?: boolean;
  sizes?: string;
  quality?: number;
  placeholder?: 'blur' | 'empty';
  blurDataURL?: string;
  fallbackSrc?: string;
  onLoad?: () => void;
  onError?: () => void;
  lazy?: boolean;
  aspectRatio?: string;
}

/**
 * Generate a blur placeholder data URL
 */
function generateBlurDataURL(width = 10, height = 10): string {
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;

  const ctx = canvas.getContext('2d');
  if (!ctx) return '';

  // Create a simple gradient blur effect
  const gradient = ctx.createLinearGradient(0, 0, width, height);
  gradient.addColorStop(0, '#f3f4f6');
  gradient.addColorStop(0.5, '#e5e7eb');
  gradient.addColorStop(1, '#d1d5db');

  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, width, height);

  return canvas.toDataURL();
}

/**
 * Default blur placeholder for consistent loading experience
 */
const DEFAULT_BLUR_DATA_URL =
  'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=';

/**
 * Intersection Observer hook for lazy loading
 */
function useIntersectionObserver(
  elementRef: React.RefObject<HTMLElement>,
  options: IntersectionObserverInit = {}
) {
  const [isIntersecting, setIsIntersecting] = useState(false);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsIntersecting(entry.isIntersecting);
      },
      {
        threshold: 0.1,
        rootMargin: '50px',
        ...options,
      }
    );

    observer.observe(element);

    return () => {
      observer.unobserve(element);
    };
  }, [elementRef, options]);

  return isIntersecting;
}

/**
 * OptimizedImage Component
 */
export function OptimizedImage({
  src,
  alt,
  width,
  height,
  className,
  priority = false,
  fill = false,
  sizes = '(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw',
  quality = 85,
  placeholder = 'blur',
  blurDataURL,
  fallbackSrc = '/images/placeholder.jpg',
  onLoad,
  onError,
  lazy = true,
  aspectRatio,
  ...props
}: OptimizedImageProps) {
  const [imageError, setImageError] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [loadStartTime, setLoadStartTime] = useState<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Use intersection observer for lazy loading (unless priority is set)
  const isIntersecting = useIntersectionObserver(containerRef, {
    threshold: 0.1,
    rootMargin: '100px', // Start loading 100px before entering viewport
  });

  const shouldLoad = !lazy || priority || isIntersecting;

  // Handle image load success
  const handleLoad = () => {
    setImageLoaded(true);

    // Performance monitoring
    if (loadStartTime) {
      const loadTime = performance.now() - loadStartTime;
      console.log(`Image loaded in ${loadTime.toFixed(0)}ms: ${src}`);

      // Report slow loading images
      if (loadTime > 2000) {
        console.warn(`Slow image loading detected: ${src} took ${loadTime.toFixed(0)}ms`);
      }
    }

    onLoad?.();
  };

  // Handle image load error
  const handleError = () => {
    setImageError(true);
    console.warn(`Failed to load image: ${src}`);
    onError?.();
  };

  // Start timing when we begin loading
  useEffect(() => {
    if (shouldLoad && !loadStartTime) {
      setLoadStartTime(performance.now());
    }
  }, [shouldLoad, loadStartTime]);

  // Generate blur placeholder if not provided
  const effectiveBlurDataURL =
    blurDataURL || (typeof window !== 'undefined' ? generateBlurDataURL() : DEFAULT_BLUR_DATA_URL);

  // Container styles for aspect ratio
  const containerStyles = aspectRatio
    ? {
        aspectRatio,
        position: 'relative' as const,
      }
    : {};

  return (
    <div
      ref={containerRef}
      className={cn(
        'relative overflow-hidden',
        !imageLoaded && 'animate-pulse bg-gray-200',
        className
      )}
      style={containerStyles}
    >
      {shouldLoad ? (
        <Image
          src={imageError ? fallbackSrc : src}
          alt={alt}
          width={fill ? undefined : width}
          height={fill ? undefined : height}
          fill={fill}
          sizes={sizes}
          quality={quality}
          priority={priority}
          placeholder={placeholder}
          blurDataURL={placeholder === 'blur' ? effectiveBlurDataURL : undefined}
          className={cn(
            'transition-opacity duration-300',
            imageLoaded ? 'opacity-100' : 'opacity-0',
            fill && 'object-cover'
          )}
          onLoad={handleLoad}
          onError={handleError}
          {...props}
        />
      ) : (
        // Placeholder while waiting for intersection
        <div
          className={cn(
            'w-full h-full bg-gradient-to-br from-gray-100 to-gray-200',
            'flex items-center justify-center text-gray-400'
          )}
          style={{
            width: width || '100%',
            height: height || '100%',
            minHeight: aspectRatio ? 'auto' : '200px',
          }}
        >
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
        </div>
      )}

      {/* Loading indicator */}
      {shouldLoad && !imageLoaded && !imageError && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600" />
        </div>
      )}

      {/* Error state */}
      {imageError && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 text-gray-500">
          <div className="text-center">
            <svg
              className="w-8 h-8 mx-auto mb-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
              />
            </svg>
            <p className="text-xs">Failed to load</p>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Specialized components for common use cases
 */

// Avatar image with circular crop
export function OptimizedAvatar({
  src,
  alt,
  size = 40,
  className,
  ...props
}: Omit<OptimizedImageProps, 'width' | 'height'> & { size?: number }) {
  return (
    <OptimizedImage
      src={src}
      alt={alt}
      width={size}
      height={size}
      className={cn('rounded-full', className)}
      quality={90}
      {...props}
    />
  );
}

// Article thumbnail with consistent aspect ratio
export function OptimizedThumbnail({ src, alt, className, ...props }: OptimizedImageProps) {
  return (
    <OptimizedImage
      src={src}
      alt={alt}
      fill
      aspectRatio="16/9"
      className={cn('rounded-lg', className)}
      sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 25vw"
      {...props}
    />
  );
}

// Hero image with priority loading
export function OptimizedHero({ src, alt, className, ...props }: OptimizedImageProps) {
  return (
    <OptimizedImage
      src={src}
      alt={alt}
      fill
      priority
      quality={95}
      className={cn('object-cover', className)}
      sizes="100vw"
      {...props}
    />
  );
}
