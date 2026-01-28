import { Check } from 'lucide-react';

interface Step {
  id: number;
  title: string;
}

interface StepIndicatorProps {
  steps: Step[];
  currentStep: number;
}

export default function StepIndicator({ steps, currentStep }: StepIndicatorProps) {
  return (
    <div className="flex items-center justify-center mb-8">
      {steps.map((step, index) => (
        <div key={step.id} className="flex items-center">
          {/* Step Circle */}
          <div className="flex flex-col items-center">
            <div
              className={`
                w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium
                sidebar-transition
                ${currentStep > step.id
                  ? 'bg-gray-900 text-white'
                  : currentStep === step.id
                    ? 'bg-gray-900 text-white'
                    : 'bg-gray-200 text-gray-500'
                }
              `}
            >
              {currentStep > step.id ? (
                <Check size={18} strokeWidth={2.5} />
              ) : (
                step.id
              )}
            </div>
            <span
              className={`
                mt-2 text-xs font-medium
                ${currentStep >= step.id ? 'text-gray-900' : 'text-gray-400'}
              `}
            >
              {step.title}
            </span>
          </div>

          {/* Connector Line */}
          {index < steps.length - 1 && (
            <div
              className={`
                w-16 h-0.5 mx-3 mt-[-20px]
                ${currentStep > step.id ? 'bg-gray-900' : 'bg-gray-200'}
              `}
            />
          )}
        </div>
      ))}
    </div>
  );
}
