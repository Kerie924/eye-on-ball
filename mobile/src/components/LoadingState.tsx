import { ActivityIndicator, StyleSheet, Text, View } from 'react-native'

import { colors } from '../theme/colors'

export function LoadingState({ message = 'Carregando...' }: { message?: string }) {
  return (
    <View style={styles.wrap}>
      <ActivityIndicator size="large" color={colors.grass} />
      <Text style={styles.text}>{message}</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    padding: 24,
    backgroundColor: colors.black,
  },
  text: {
    color: colors.textSecondary,
    fontSize: 15,
  },
})
