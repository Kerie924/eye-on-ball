import { Image, StyleSheet, type ImageStyle, type StyleProp } from 'react-native'

const companyLogo = require('../../assets/images/brand/company-logo.png')
const mark = require('../../assets/images/brand/mark.png')
const wordmark = require('../../assets/images/brand/wordmark.png')

type BrandVariant = 'full' | 'mark' | 'wordmark'

interface BrandLogoProps {
  variant?: BrandVariant
  height?: number
  style?: StyleProp<ImageStyle>
}

const ASPECT: Record<BrandVariant, number> = {
  full: 371 / 108,
  mark: 250 / 268,
  wordmark: 670 / 135,
}

const SOURCE: Record<BrandVariant, number> = {
  full: companyLogo,
  mark: mark,
  wordmark: wordmark,
}

export function BrandLogo({ variant = 'full', height = 56, style }: BrandLogoProps) {
  const width = Math.round(height * ASPECT[variant])
  return (
    <Image
      source={SOURCE[variant]}
      style={[{ width, height }, style]}
      resizeMode="contain"
      accessibilityLabel="Olho no Lance"
    />
  )
}
