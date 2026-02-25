/**
 * Tests for useFormState composable.
 */
import { describe, it, expect } from 'vitest'
import { useFormState } from './useFormState'

describe('useFormState', () => {
  const defaults = {
    name: '',
    email: '',
    scale_length_mm: 650,
  }

  it('initializes with cloned defaults', () => {
    const { form, errors, touched, isDirty } = useFormState(defaults)
    expect(form.value).toEqual(defaults)
    expect(errors.value).toEqual({})
    expect(touched.value).toEqual({})
    expect(isDirty.value).toBe(false)
  })

  it('does not share references with original defaults', () => {
    const { form } = useFormState(defaults)
    form.value.name = 'changed'
    expect(defaults.name).toBe('')
  })

  it('isDirty becomes true when field changes', () => {
    const { form, isDirty } = useFormState(defaults)
    form.value.name = 'Stratocaster'
    expect(isDirty.value).toBe(true)
  })

  it('isDirty returns false when values match defaults', () => {
    const { form, isDirty } = useFormState(defaults)
    form.value.name = 'changed'
    expect(isDirty.value).toBe(true)
    form.value.name = ''
    expect(isDirty.value).toBe(false)
  })

  it('setField updates value and marks touched', () => {
    const { form, touched, setField } = useFormState(defaults)
    setField('email', 'luthier@example.com')
    expect(form.value.email).toBe('luthier@example.com')
    expect(touched.value.email).toBe(true)
  })

  it('setField does not mark other fields as touched', () => {
    const { touched, setField } = useFormState(defaults)
    setField('name', 'test')
    expect(touched.value.name).toBe(true)
    expect(touched.value.email).toBeUndefined()
    expect(touched.value.scale_length_mm).toBeUndefined()
  })

  it('reset restores defaults and clears state', () => {
    const { form, errors, touched, isDirty, setField, setError, reset } = useFormState(defaults)

    setField('name', 'Fender')
    setField('scale_length_mm', 647.7)
    setError('email', 'Required')

    expect(isDirty.value).toBe(true)

    reset()

    expect(form.value).toEqual(defaults)
    expect(errors.value).toEqual({})
    expect(touched.value).toEqual({})
    expect(isDirty.value).toBe(false)
  })

  it('setError adds and removes per-field errors', () => {
    const { errors, setError } = useFormState(defaults)

    setError('name', 'Name is required')
    expect(errors.value.name).toBe('Name is required')

    setError('name', undefined)
    expect(errors.value.name).toBeUndefined()
  })

  it('clearErrors removes all errors at once', () => {
    const { errors, setError, clearErrors } = useFormState(defaults)
    setError('name', 'Required')
    setError('email', 'Invalid email')
    expect(Object.keys(errors.value).length).toBe(2)

    clearErrors()
    expect(errors.value).toEqual({})
  })

  it('touch marks a field without changing its value', () => {
    const { form, touched, touch } = useFormState(defaults)
    touch('email')
    expect(touched.value.email).toBe(true)
    expect(form.value.email).toBe('')
  })

  it('handles nested object defaults via deep clone', () => {
    const nested = {
      config: { nested: true },
      label: 'test',
    }
    const { form, isDirty, reset } = useFormState(nested)

    form.value.config = { nested: false }
    expect(isDirty.value).toBe(true)

    reset()
    expect(form.value.config).toEqual({ nested: true })
    expect(isDirty.value).toBe(false)
  })

  it('accepts custom clone function', () => {
    const customClone = <T>(v: T): T => structuredClone(v)
    const { form, reset } = useFormState(defaults, { clone: customClone })

    form.value.name = 'custom'
    reset()
    expect(form.value.name).toBe('')
  })

  it('multiple resets are idempotent', () => {
    const { form, isDirty, reset, setField } = useFormState(defaults)
    setField('name', 'test')
    reset()
    reset()
    reset()
    expect(form.value).toEqual(defaults)
    expect(isDirty.value).toBe(false)
  })

  it('isDirty correctly handles numeric zero vs default zero', () => {
    const numDefaults = { count: 0, label: '' }
    const { isDirty } = useFormState(numDefaults)
    // No changes — should not be dirty
    expect(isDirty.value).toBe(false)
  })
})
