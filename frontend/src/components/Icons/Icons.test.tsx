import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ShieldIcon, SearchIcon, EyeIcon, BoltIcon, LogOutIcon, KeyIcon } from './Icons'

describe('Icon Components', () => {
  it('renders ShieldIcon without crashing', () => {
    render(<ShieldIcon size={24} />)
    const svg = document.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })

  it('renders SearchIcon without crashing', () => {
    render(<SearchIcon size={24} />)
    const svg = document.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })

  it('renders EyeIcon without crashing', () => {
    render(<EyeIcon size={24} />)
    const svg = document.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })

  it('renders BoltIcon without crashing', () => {
    render(<BoltIcon size={24} />)
    const svg = document.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })

  it('renders LogOutIcon without crashing', () => {
    render(<LogOutIcon size={24} />)
    const svg = document.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })

  it('renders KeyIcon without crashing', () => {
    render(<KeyIcon size={24} />)
    const svg = document.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })

  it('applies custom size prop', () => {
    render(<ShieldIcon size={48} />)
    const svg = document.querySelector('svg')
    expect(svg).toHaveAttribute('width', '48')
    expect(svg).toHaveAttribute('height', '48')
  })

  it('applies custom color prop', () => {
    render(<ShieldIcon size={24} color="red" />)
    const svg = document.querySelector('svg')
    expect(svg).toHaveAttribute('stroke', 'red')
  })
})
