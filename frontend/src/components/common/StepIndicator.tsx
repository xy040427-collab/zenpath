import { getChineseOrdinal } from '../../utils/formatters';

interface StepIndicatorProps {
  currentStep: number;
  totalSteps: number;
  labels: string[];
}

export default function StepIndicator({ currentStep, totalSteps, labels }: StepIndicatorProps) {
  return (
    <div className="flex items-center justify-center gap-4 font-mono text-caption-mono">
      {Array.from({ length: totalSteps }, (_, i) => i + 1).map((step) => (
        <div key={step} className="flex items-center gap-2">
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300 ${
              step === currentStep
                ? 'bg-accent-gold text-brand-900'
                : step < currentStep
                ? 'bg-brand-700 text-white'
                : 'bg-beige-200 text-beige-600'
            }`}
          >
            {step < currentStep ? (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            ) : (
              <span className="text-xs">{step}</span>
            )}
          </div>
          <span
            className={`hidden sm:block text-[10px] uppercase tracking-[0.2em] ${
              step === currentStep ? 'text-brand-900' : 'text-beige-500'
            }`}
          >
            {labels[step - 1] || `${getChineseOrdinal(step)}步`}
          </span>
          {step < totalSteps && (
            <div className="hidden sm:block w-12 h-px bg-beige-300 mx-2" />
          )}
        </div>
      ))}
    </div>
  );
}
