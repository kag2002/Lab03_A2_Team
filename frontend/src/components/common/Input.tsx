import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  className = '',
  ...props
}) => {
  return (
    <div className="w-full flex flex-col gap-1.5">
      {label && (
        <label className="text-xs font-semibold text-slate-400 select-none px-0.5">
          {label}
        </label>
      )}
      <input
        className={`w-full px-4 py-3 bg-[#0d1222] border border-slate-700/60 rounded-xl text-slate-100 placeholder-slate-500 text-sm transition-all duration-300 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500/30 ${className}`}
        {...props}
      />
      {error && (
        <span className="text-xs text-red-400 px-0.5">
          {error}
        </span>
      )}
    </div>
  );
};
