import { Clock } from 'lucide-react';

interface Props {
  title: string;
  description?: string;
  details?: string[];
}

export default function ComingSoon({ title, description, details }: Props) {
  return (
    <div className="coming-soon">
      <div className="coming-soon-icon">
        <Clock size={36} />
      </div>
      <h3 className="coming-soon-title">{title}</h3>
      {description && <p className="coming-soon-desc">{description}</p>}
      {details && details.length > 0 && (
        <ul className="coming-soon-list">
          {details.map((d, i) => <li key={i}>{d}</li>)}
        </ul>
      )}
      <span className="coming-soon-badge">개발 예정</span>
    </div>
  );
}
