import React from 'react';

export default function FormInput({ label, id, type = 'text', required = false, value, onChange, placeholder, className = '' }) {
  return (
    <div className="mb-4">
      <label htmlFor={id} className="block text-sm font-medium text-slate-700 mb-1">
        {label}{required && <span className="text-red-600 ml-1">*</span>}
      </label>
      <input
        id={id}
        name={id}
        type={type}
        required={required}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className={`w-full rounded-none border border-slate-300 bg-white px-3 py-2 text-base focus:border-primary-600 focus:ring-2 focus:ring-primary-200 outline-none ${className}`}
      />
    </div>
  );
}
