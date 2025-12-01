import React from 'react'

function DateRangePicker({ value, onChange }) {
  const options = [
    { label: 'Last 24 Hours', value: 1 },
    { label: 'Last 7 Days', value: 7 },
    { label: 'Last 30 Days', value: 30 },
    { label: 'Last 90 Days', value: 90 }
  ]

  return (
    <select 
      value={value} 
      onChange={(e) => onChange(parseInt(e.target.value))}
      className="date-range-picker"
    >
      {options.map(option => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  )
}

export default DateRangePicker