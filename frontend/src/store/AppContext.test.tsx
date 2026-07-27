import { describe, it, expect, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { ReactNode } from 'react'
import { AppProvider, useApp } from './AppContext'

// Wrapper component for hooks that need context
const wrapper = ({ children }: { children: ReactNode }) => (
  <AppProvider>{children}</AppProvider>
)

describe('AppContext', () => {
  it('provides initial state', () => {
    const { result } = renderHook(() => useApp(), { wrapper })
    
    expect(result.current.state.searchQuery).toBe('')
    expect(result.current.state.isSearching).toBe(false)
    expect(result.current.state.results).toEqual([])
    expect(result.current.state.activeTab).toBe('search')
  })

  it('provides dispatch function', () => {
    const { result } = renderHook(() => useApp(), { wrapper })
    expect(typeof result.current.dispatch).toBe('function')
  })

  it('provides runSearch function', () => {
    const { result } = renderHook(() => useApp(), { wrapper })
    expect(typeof result.current.runSearch).toBe('function')
  })

  it('updates search query via dispatch', () => {
    const { result } = renderHook(() => useApp(), { wrapper })
    
    act(() => {
      result.current.dispatch({ type: 'SET_SEARCH_QUERY', payload: 'example.com' })
    })
    
    expect(result.current.state.searchQuery).toBe('example.com')
  })

  it('updates active tab via dispatch', () => {
    const { result } = renderHook(() => useApp(), { wrapper })
    
    act(() => {
      result.current.dispatch({ type: 'SET_ACTIVE_TAB', payload: 'watches' })
    })
    
    expect(result.current.state.activeTab).toBe('watches')
  })

  it('adds toast notifications', () => {
    const { result } = renderHook(() => useApp(), { wrapper })
    
    act(() => {
      result.current.dispatch({
        type: 'ADD_TOAST',
        payload: { id: 1, message: 'Test toast', type: 'info', icon: 'ℹ️' }
      })
    })
    
    expect(result.current.state.toasts).toHaveLength(1)
    expect(result.current.state.toasts[0].message).toBe('Test toast')
  })

  it('removes toast notifications', () => {
    const { result } = renderHook(() => useApp(), { wrapper })
    
    act(() => {
      result.current.dispatch({
        type: 'ADD_TOAST',
        payload: { id: 1, message: 'Test', type: 'info', icon: 'ℹ️' }
      })
    })
    
    act(() => {
      result.current.dispatch({ type: 'REMOVE_TOAST', payload: 1 })
    })
    
    expect(result.current.state.toasts).toHaveLength(0)
  })

  it('limits toasts to 5', () => {
    const { result } = renderHook(() => useApp(), { wrapper })
    
    act(() => {
      for (let i = 1; i <= 6; i++) {
        result.current.dispatch({
          type: 'ADD_TOAST',
          payload: { id: i, message: `Toast ${i}`, type: 'info', icon: 'ℹ️' }
        })
      }
    })
    
    expect(result.current.state.toasts).toHaveLength(5)
  })

  it('throws when used outside provider', () => {
    // Suppress console.error for this test
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    
    expect(() => {
      renderHook(() => useApp())
    }).toThrow('useApp must be used within AppProvider')
    
    consoleSpy.mockRestore()
  })
})
