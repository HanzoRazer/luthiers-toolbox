/**
 * Composable for startup planning calculations.
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'

// ============================================================================
// Types
// ============================================================================

export interface StartupData {
  cncCost: number
  handTools: number
  workbenches: number
  rent: number
  utilities: number
  loanAmount: number
  interestRate: number
  loanTermYears: number
  loanStartDate: string
}

export interface AmortizationEntry {
  number: number
  date: string
  principal: number
  interest: number
  balance: number
}

export interface StartupCalculatorState {
  startup: Ref<StartupData>
  showAmortization: Ref<boolean>
  totalEquipment: ComputedRef<number>
  monthlyOverhead: ComputedRef<number>
  firstYearCost: ComputedRef<number>
  monthlyPayment: ComputedRef<number>
  totalLoanPayment: ComputedRef<number>
  totalInterest: ComputedRef<number>
  amortizationSchedule: ComputedRef<AmortizationEntry[]>
}

// ============================================================================
// Composable
// ============================================================================

export function useStartupCalculator(): StartupCalculatorState {
  const startup = ref<StartupData>({
    cncCost: 15000,
    handTools: 2000,
    workbenches: 1500,
    rent: 800,
    utilities: 200,
    loanAmount: 15000,
    interestRate: 7.5,
    loanTermYears: 5,
    loanStartDate: new Date().toISOString().slice(0, 7)
  })

  const showAmortization = ref(false)

  const totalEquipment = computed(() =>
    startup.value.cncCost + startup.value.handTools + startup.value.workbenches
  )

  const monthlyOverhead = computed(() =>
    startup.value.rent + startup.value.utilities
  )

  const firstYearCost = computed(() =>
    totalEquipment.value + monthlyOverhead.value * 12
  )

  const monthlyPayment = computed(() => {
    const P = startup.value.loanAmount
    const r = startup.value.interestRate / 100 / 12
    const n = startup.value.loanTermYears * 12

    if (r === 0) return P / n

    return P * (r * Math.pow(1 + r, n)) / (Math.pow(1 + r, n) - 1)
  })

  const totalLoanPayment = computed(() =>
    monthlyPayment.value * startup.value.loanTermYears * 12
  )

  const totalInterest = computed(() =>
    totalLoanPayment.value - startup.value.loanAmount
  )

  const amortizationSchedule = computed(() => {
    const schedule: AmortizationEntry[] = []
    let balance = startup.value.loanAmount
    const monthlyRate = startup.value.interestRate / 100 / 12
    const totalPayments = startup.value.loanTermYears * 12
    const payment = monthlyPayment.value

    const [year, month] = startup.value.loanStartDate.split('-').map(Number)
    const currentDate = new Date(year, month - 1, 1)

    for (let i = 1; i <= totalPayments; i++) {
      const interestPayment = balance * monthlyRate
      const principalPayment = payment - interestPayment
      balance -= principalPayment

      schedule.push({
        number: i,
        date: currentDate.toLocaleDateString('en-US', { year: 'numeric', month: 'short' }),
        principal: principalPayment,
        interest: interestPayment,
        balance: Math.max(0, balance)
      })

      currentDate.setMonth(currentDate.getMonth() + 1)
    }

    return schedule
  })

  return {
    startup,
    showAmortization,
    totalEquipment,
    monthlyOverhead,
    firstYearCost,
    monthlyPayment,
    totalLoanPayment,
    totalInterest,
    amortizationSchedule
  }
}
