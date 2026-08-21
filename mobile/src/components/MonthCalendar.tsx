import { Pressable, StyleSheet, Text, View } from 'react-native'

import { colors } from '../theme/colors'

const WEEKDAYS = ['D', 'S', 'T', 'Q', 'Q', 'S', 'S']

function daysInMonth(year: number, monthIndex: number) {
  return new Date(year, monthIndex + 1, 0).getDate()
}

function toDateString(year: number, monthIndex: number, day: number) {
  return `${year}-${String(monthIndex + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
}

interface MonthCalendarProps {
  value: string
  onChange: (date: string) => void
}

export function MonthCalendar({ value, onChange }: MonthCalendarProps) {
  const selected = value ? new Date(`${value}T12:00:00`) : new Date()
  const year = selected.getFullYear()
  const monthIndex = selected.getMonth()
  const firstWeekday = new Date(year, monthIndex, 1).getDay()
  const totalDays = daysInMonth(year, monthIndex)
  const today = toDateString(
    new Date().getFullYear(),
    new Date().getMonth(),
    new Date().getDate(),
  )

  const cells: Array<number | null> = [
    ...Array.from({ length: firstWeekday }, () => null),
    ...Array.from({ length: totalDays }, (_, index) => index + 1),
  ]

  const title = selected.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })

  function shiftMonth(delta: number) {
    const next = new Date(year, monthIndex + delta, 1)
    onChange(toDateString(next.getFullYear(), next.getMonth(), 1))
  }

  return (
    <View style={styles.wrap}>
      <View style={styles.header}>
        <Pressable onPress={() => shiftMonth(-1)} hitSlop={8}>
          <Text style={styles.nav}>‹</Text>
        </Pressable>
        <Text style={styles.title}>{title}</Text>
        <Pressable onPress={() => shiftMonth(1)} hitSlop={8}>
          <Text style={styles.nav}>›</Text>
        </Pressable>
      </View>
      <View style={styles.weekRow}>
        {WEEKDAYS.map((label, index) => (
          <Text key={`${label}-${index}`} style={styles.weekday}>
            {label}
          </Text>
        ))}
      </View>
      <View style={styles.grid}>
        {cells.map((day, index) => {
          if (!day) {
            return <View key={`empty-${index}`} style={styles.cell} />
          }
          const date = toDateString(year, monthIndex, day)
          const isSelected = date === value
          const isToday = date === today
          return (
            <Pressable
              key={date}
              style={[styles.cell, isSelected && styles.cellSelected, isToday && !isSelected && styles.cellToday]}
              onPress={() => onChange(date)}
            >
              <Text style={[styles.day, isSelected && styles.daySelected]}>{day}</Text>
            </Pressable>
          )
        })}
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    backgroundColor: colors.card,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    padding: 14,
    gap: 10,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  title: {
    color: colors.white,
    fontWeight: '800',
    fontSize: 16,
    textTransform: 'capitalize',
  },
  nav: {
    color: colors.grassBright,
    fontSize: 28,
    fontWeight: '300',
    paddingHorizontal: 8,
  },
  weekRow: {
    flexDirection: 'row',
  },
  weekday: {
    flex: 1,
    textAlign: 'center',
    color: colors.textMuted,
    fontSize: 12,
    fontWeight: '700',
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  cell: {
    width: '14.285%',
    aspectRatio: 1,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 999,
  },
  cellSelected: {
    backgroundColor: colors.grass,
  },
  cellToday: {
    borderWidth: 1,
    borderColor: colors.grass,
  },
  day: {
    color: colors.white,
    fontWeight: '600',
  },
  daySelected: {
    color: colors.textOnGreen,
  },
})
