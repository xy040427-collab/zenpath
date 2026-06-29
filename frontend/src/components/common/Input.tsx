import { type InputHTMLAttributes, forwardRef } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, className = '', ...props }, ref) => {
    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label className="font-sans text-sm font-normal text-brand-900/80 tracking-wide">
            {label}
          </label>
        )}
        <input
          ref={ref}
          className={`
            w-full px-4 py-3 bg-white border rounded-lg
            font-sans font-light text-brand-900 text-base
            placeholder:text-beige-500
            transition-colors duration-200
            focus:outline-none focus:ring-2 focus:ring-brand-400/30 focus:border-brand-400
            ${error ? 'border-accent-ruby' : 'border-stone'}
            ${className}
          `}
          {...props}
        />
        {error && (
          <span className="font-sans text-xs text-accent-ruby">{error}</span>
        )}
        {hint && !error && (
          <span className="font-sans text-xs text-beige-600">{hint}</span>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;
