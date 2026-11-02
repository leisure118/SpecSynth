/**
 * Small, reusable presentation helpers. These only set CSS custom properties;
 * layout and content stay in the view layer.
 */

export function spotlight(event) {
  const element = event.currentTarget
  const rect = element.getBoundingClientRect()
  element.style.setProperty('--mx', `${event.clientX - rect.left}px`)
  element.style.setProperty('--my', `${event.clientY - rect.top}px`)
}

export function particleStyle(index, { left = 37, top = 53, span = 94, maxY = 82 } = {}) {
  return {
    left: `${((index * left) % span) + 3}%`,
    top: `${((index * top) % maxY) + 6}%`,
    '--size': `${2 + (index % 3)}px`,
    '--dur': `${11 + (index % 7) * 2}s`,
    '--delay': `${-(index % 9) * 1.4}s`,
  }
}
