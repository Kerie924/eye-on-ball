import { StyleSheet, View } from 'react-native'

import { BrandLogo } from './BrandLogo'
import { colors } from '../theme/colors'

interface AppBrandHeaderProps {
  /** Compact mark+wordmark for in-app screens; full for auth. */
  compact?: boolean
}

export function AppBrandHeader({ compact = true }: AppBrandHeaderProps) {
  if (!compact) {
    return (
      <View style={styles.fullWrap}>
        <BrandLogo variant="full" width={340} />
      </View>
    )
  }

  return (
    <View style={styles.compactWrap}>
      <BrandLogo variant="full" width={280} />
    </View>
  )
}

const styles = StyleSheet.create({
  fullWrap: {
    alignItems: 'center',
    justifyContent: 'center',
    width: '100%',
  },
  compactWrap: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 6,
    paddingBottom: 8,
    paddingHorizontal: 12,
    backgroundColor: colors.black,
  },
})
