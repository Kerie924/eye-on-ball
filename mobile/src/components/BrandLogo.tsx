import { Image, type ImageStyle, type StyleProp } from 'react-native'

const companyLogo = require('../../assets/images/brand/company-logo.png')
const mark = require('../../assets/images/brand/mark.png')
const wordmark = require('../../assets/images/brand/wordmark.png')

type BrandVariant = 'full' | 'mark' | 'wordmark'

interface BrandLogoProps {
  variant?: BrandVariant
  /** Used when `width` is not set. */
  height?: number
  /** Preferred for full/wordmark logos so they scale up on phone screens. */
  width?: number
  style?: StyleProp<ImageStyle>
}

const ASPECT: Record<BrandVariant, number> = {
  full: 1526 / 981,
  mark: 1502 / 979,
  wordmark: 1442 / 240,
}

const SOURCE: Record<BrandVariant, number> = {
  full: companyLogo,
  mark: mark,
  wordmark: wordmark,
}

export function BrandLogo({
  variant = 'full',
  height = 56,
  width,
  style,
}: BrandLogoProps) {
  const aspect = ASPECT[variant]
  const resolvedWidth = width ?? Math.round(height * aspect)
  const resolvedHeight = width ? Math.round(width / aspect) : height

  return (
    <Image
      source={SOURCE[variant]}
      style={[{ width: resolvedWidth, height: resolvedHeight }, style]}
      resizeMode="contain"
      accessibilityLabel="Lance On"
    />
  )
}
