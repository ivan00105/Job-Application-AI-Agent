/**
 * Radar Chart Component - Displays profile scores across 6 dimensions
 */
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Legend } from 'recharts';

interface RadarChartProps {
  scores: {
    qualification: number;
    experience: number;
    technical_skills: number;
    soft_skills: number;
    tools_platforms: number;
    industry_knowledge: number;
  };
}

export const ProfileRadarChart = ({ scores }: RadarChartProps) => {
  // Transform scores for recharts format
  const data = [
    {
      dimension: 'Qualification',
      score: Math.round(scores.qualification),
      fullMark: 100,
    },
    {
      dimension: 'Experience',
      score: Math.round(scores.experience),
      fullMark: 100,
    },
    {
      dimension: 'Technical Skills',
      score: Math.round(scores.technical_skills),
      fullMark: 100,
    },
    {
      dimension: 'Soft Skills',
      score: Math.round(scores.soft_skills),
      fullMark: 100,
    },
    {
      dimension: 'Tools & Platforms',
      score: Math.round(scores.tools_platforms),
      fullMark: 100,
    },
    {
      dimension: 'Industry Knowledge',
      score: Math.round(scores.industry_knowledge),
      fullMark: 100,
    },
  ];

  return (
    <div className="w-full h-96">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data}>
          <PolarGrid />
          <PolarAngleAxis 
            dataKey="dimension" 
            tick={{ fontSize: 12, fill: '#4B5563' }}
            style={{ textTransform: 'none' }}
          />
          <PolarRadiusAxis 
            angle={90} 
            domain={[0, 100]}
            tick={{ fontSize: 10, fill: '#9CA3AF' }}
            tickCount={6}
          />
          <Radar
            name="Your Profile"
            dataKey="score"
            stroke="#3B82F6"
            fill="#3B82F6"
            fillOpacity={0.6}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
};

