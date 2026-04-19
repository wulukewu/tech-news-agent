'use client';

import * as React from 'react';
import Image from 'next/image';
import { cn } from '@/lib/utils';
import { useResponsiveLayout } from '@/hooks/useResponsiveLayout';
import { useI18n } from '@/contexts/I18nContext';

interface OptimizedImageProps {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  fill?: boolean;
  priority?: boolean;
  quality?: number;
  placeholder?: 'blur' | 'empty';
  blurDataURL?: string;
  className?: string;
  sizes?: string;
  onLoad?: () => void;
  onError?: () => void;
  fallbackSrc?: string;
  adaptiveQuality?: boolean;
}

/**
 * OptimizedImage - Enhanced Next.js Image component with mobile optimization
 * Provides automatic optimization, lazy loading, adaptive quality, and fallback support
 */
export function OptimizedImage({
  src,
  alt,
  width,
  height,
  fill = false,
  priority = false,
  quality = 75,
  placeholder = 'empty',
  blurDataURL,
  className,
  sizes,
  onLoad,
  onError,
  fallbackSrc = '/images/placeholder.jpg',
  adaptiveQuality = true,
}: OptimizedImageProps) {
  const { t } = useI18n();
  const [imageSrc, setImageSrc] = React.useState(src);
  const [isLoading, setIsLoading] = React.useState(true);
  const [hasError, setHasError] = React.useState(false);
  const { deviceType } = useResponsiveLayout();

  // Reset state when src changes
  React.useEffect(() => {
    setImageSrc(src);
    setIsLoading(true);
    setHasError(false);
  }, [src]);

  // Adaptive quality based on device and connection
  const getOptimizedQuality = () => {
    if (!adaptiveQuality) return quality;

    // Check for slow connection
    const connection = (navigator as any).connection;
    const isSlowConnection =
      connection &&
      (connection.effectiveType === 'slow-2g' ||
        connection.effectiveType === '2g' ||
        connection.saveData);

    if (isSlowConnection) {
      return Math.min(quality, 60); // Lower quality for slow connections
    } else if (deviceType === 'mobile') {
      return Math.min(quality, 75); // Medium quality for mobile
    } else {
      return quality; // Original quality for desktop
    }
  };

  // Generate responsive sizes if not provided
  const getResponsiveSizes = () => {
    if (sizes) return sizes;

    if (deviceType === 'mobile') {
      return '(max-width: 768px) 100vw, 50vw';
    } else if (deviceType === 'tablet') {
      return '(max-width: 1024px) 50vw, 33vw';
    } else {
      return '(max-width: 1280px) 33vw, 25vw';
    }
  };

  const handleLoad = () => {
    setIsLoading(false);
    onLoad?.();
  };

  const handleError = () => {
    setHasError(true);
    setIsLoading(false);

    // Try fallback image if available and not already using it
    if (fallbackSrc && imageSrc !== fallbackSrc) {
      setImageSrc(fallbackSrc);
      setHasError(false);
      setIsLoading(true);
    }

    onError?.();
  };

  // Generate blur data URL for placeholder
  const getBlurDataURL = () => {
    if (blurDataURL) return blurDataURL;

    // Generate a simple blur data URL
    return 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=';
  };

  const imageProps = {
    src: imageSrc,
    alt,
    onLoad: handleLoad,
    onError: handleError,
    quality: getOptimizedQuality(),
    priority,
    placeholder: placeholder === 'blur' ? ('blur' as const) : ('empty' as const),
    ...(placeholder === 'blur' && { blurDataURL: getBlurDataURL() }),
    className: cn(
      'transition-opacity duration-300',
      isLoading && 'opacity-0',
      !isLoading && 'opacity-100',
      className
    ),
    sizes: getResponsiveSizes(),
  };

  if (fill) {
    return (
      <div className="relative overflow-hidden">
        <Image {...imageProps} fill style={{ objectFit: 'cover' }} />
        {isLoading && <div className="absolute inset-0 bg-muted animate-pulse" />}
        {hasError && !fallbackSrc && (
          <div className="absolute inset-0 bg-muted flex items-center justify-center">
            <span className="text-muted-foreground text-sm">{t('ui.image-load-failed')}</span>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="relative">
      <Image {...imageProps} width={width} height={height} />
      {isLoading && (
        <div className="absolute inset-0 bg-muted animate-pulse" style={{ width, height }} />
      )}
      {hasError && !fallbackSrc && (
        <div
          className="absolute inset-0 bg-muted flex items-center justify-center"
          style={{ width, height }}
        >
          <span className="text-muted-foreground text-sm">{t('ui.image-load-failed')}</span>
        </div>
      )}
    </div>
  );
}

// Preset image components for common use cases with mobile optimization
export function OptimizedAvatarImage({
  src,
  alt,
  size = 40,
  ...props
}: OptimizedImageProps & { size?: number }) {
  return (
    <OptimizedImage
      src={src}
      alt={alt}
      width={size}
      height={size}
      className={cn('rounded-full', props.className)}
      quality={90} // Higher quality for avatars
      adaptiveQuality={true}
      {...props}
    />
  );
}

export function ArticleImage({ src, alt, ...props }: OptimizedImageProps) {
  return (
    <OptimizedImage
      src={src}
      alt={alt}
      width={400}
      height={225}
      className={cn('rounded-lg object-cover', props.className)}
      sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 400px"
      adaptiveQuality={true}
      {...props}
    />
  );
}

export function HeroImage({ src, alt, ...props }: OptimizedImageProps) {
  return (
    <OptimizedImage
      src={src}
      alt={alt}
      fill
      priority
      className={cn('object-cover', props.className)}
      sizes="100vw"
      quality={85}
      adaptiveQuality={true}
      {...props}
    />
  );
}

/**
 * Mobile-optimized card image with responsive aspect ratio
 */
export function MobileCardImage({
  src,
  alt,
  aspectRatio = '16/9',
  className,
  ...props
}: OptimizedImageProps & { aspectRatio?: string }) {
  return (
    <div className={cn('relative overflow-hidden rounded-lg', className)} style={{ aspectRatio }}>
      <OptimizedImage
        src={src}
        alt={alt}
        fill
        quality={75}
        adaptiveQuality={true}
        sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
        className="object-cover"
        {...props}
      />
    </div>
  );
}

/**
 * Thumbnail image optimized for mobile lists
 */
export function ThumbnailImage({
  src,
  alt,
  size = 60,
  ...props
}: OptimizedImageProps & { size?: number }) {
  return (
    <OptimizedImage
      src={src}
      alt={alt}
      width={size}
      height={size}
      className={cn('rounded object-cover', props.className)}
      quality={70}
      adaptiveQuality={true}
      sizes={`${size}px`}
      {...props}
    />
  );
}
