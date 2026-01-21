type IconProps = {
  className?: string;
};

export default function UploadVacancyIcon({ className }: IconProps) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <rect x="3.5" y="4" width="17" height="15" rx="2.5" />
      <path d="M12 15V8" />
      <path d="M8.5 11.5 12 8l3.5 3.5" />
    </svg>
  );
}
