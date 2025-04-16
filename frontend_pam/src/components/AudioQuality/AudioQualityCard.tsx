import { Link } from '@tanstack/react-router';
import { Button } from '@/components/ui/button';
import { DataFile } from "@/types";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js/auto';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface AudioQualityCardProps {
  dataFile: DataFile;
  deviceId: string;
  onCheckQuality: () => void;
}

const AudioQualityCard: React.FC<AudioQualityCardProps> = ({ dataFile, deviceId, onCheckQuality }) => {
  const getObservationCount = (dataFile: DataFile): number => {
    if (!dataFile.extraData?.auto_detected_observations) return 0;
    return dataFile.extraData.auto_detected_observations.length;
  };

  console.log('AudioQualityCard data:', {
    extraData: dataFile.extraData,
    observations: dataFile.extraData?.auto_detected_observations,
    count: getObservationCount(dataFile)
  });

  const getQualityColor = (score: number | null) => {
    if (score === null) return 'bg-gray-200';
    if (score >= 80) return 'bg-green-100';
    if (score >= 60) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatMetricValue = (value: number, label: string): string => {
    if (label.includes('ratio')) return `${(value * 100).toFixed(1)}%`;
    if (label.includes('mean')) return value.toFixed(2);
    return value.toString();
  };

  const renderTemporalEvolution = () => {
    if (!dataFile.extraData?.temporal_evolution) return null;
    
    const temporalData = dataFile.extraData.temporal_evolution;
    if (!temporalData.times || !Array.isArray(temporalData.times)) return null;

    const metrics = [
      { key: 'rms_energy' as const, label: 'RMS Energy', color: 'rgb(75, 192, 192)' },
      { key: 'spectral_centroid' as const, label: 'Spectral Centroid', color: 'rgb(255, 99, 132)' },
      { key: 'zero_crossing_rate' as const, label: 'Zero Crossing Rate', color: 'rgb(54, 162, 235)' }
    ];

    // Check if all required data arrays exist
    const hasAllData = metrics.every(metric => 
      Array.isArray(temporalData[metric.key]) && 
      temporalData[metric.key].length > 0
    );

    if (!hasAllData) return null;

    return (
      <div className="mt-6">
        <h4 className="text-sm font-semibold text-gray-600 mb-4">Temporal Evolution</h4>
        <div className="h-[500px]">
          <Line
            data={{
              labels: temporalData.times.map((t: number) => t.toFixed(1) + 's'),
              datasets: metrics.map(metric => ({
                label: metric.label,
                data: temporalData[metric.key],
                borderColor: metric.color,
                backgroundColor: metric.color,
                tension: 0.3,
                pointRadius: 0,
              }))
            }}
            options={{
              responsive: true,
              maintainAspectRatio: false,
              interaction: {
                mode: 'index',
                intersect: false,
              },
              plugins: {
                legend: {
                  position: 'top' as const,
                  labels: {
                    padding: 20,
                    font: {
                      size: 12
                    }
                  }
                }
              },
              scales: {
                x: {
                  title: {
                    display: true,
                    text: 'Time (seconds)',
                    font: {
                      size: 12
                    }
                  },
                  ticks: {
                    font: {
                      size: 11
                    }
                  }
                },
                y: {
                  beginAtZero: true,
                  ticks: {
                    font: {
                      size: 11
                    }
                  }
                }
              }
            }}
          />
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Audio Quality</h3>
        <div className="flex gap-2">
          <Button
            onClick={onCheckQuality}
            disabled={dataFile.qualityCheckStatus === 'in_progress'}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300"
          >
            {dataFile.qualityCheckStatus === 'in_progress' ? 'Checking...' : 'Check Quality'}
          </Button>
          <Link 
            to="/observations"
            search={{
              deviceId: deviceId,
              dataFileId: dataFile.id
            }}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 flex items-center gap-2"
          >
            <span>View Observations</span>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 bg-gray-50 p-4 rounded-lg">
        <div className="text-sm">
          <span className="font-semibold">Sample Rate:</span>
          <div className="mt-1">{dataFile.sampleRate ? `${dataFile.sampleRate} Hz` : 'Not available'}</div>
        </div>
        <div className="text-sm">
          <span className="font-semibold">File Length:</span>
          <div className="mt-1">{dataFile.fileLength || 'Not available'}</div>
        </div>
        <div className="text-sm">
          <span className="font-semibold">Config:</span>
          <div className="mt-1">{dataFile.config || 'Not available'}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className={`p-4 rounded-lg ${getQualityColor(dataFile.qualityScore)}`}>
          <div className="text-sm text-gray-600">Quality Score</div>
          <div className="text-2xl font-bold">
            {dataFile.qualityScore !== null ? `${dataFile.qualityScore}/100` : 'Not checked'}
          </div>
        </div>
        <div className="p-4 bg-gray-50 rounded-lg">
          <div className="text-sm text-gray-600">Status</div>
          <span className={`inline-block px-2 py-1 rounded text-sm ${getStatusBadgeColor(dataFile.qualityCheckStatus)}`}>
            {dataFile.qualityCheckStatus.charAt(0).toUpperCase() + dataFile.qualityCheckStatus.slice(1)}
          </span>
        </div>
      </div>

      {dataFile.extraData?.observations && dataFile.extraData.observations.length > 0 && (
        <div className="mt-4">
          <h4 className="text-sm font-semibold text-gray-600 mb-2">Observations:</h4>
          <ul className="list-disc list-inside space-y-1">
            {dataFile.extraData.observations.map((observation: string, index: number) => (
              <li key={index} className="text-sm text-gray-700">{observation}</li>
            ))}
          </ul>
        </div>
      )}

      {dataFile.qualityIssues && dataFile.qualityIssues.length > 0 && (
        <div className="mt-4">
          <h4 className="text-sm font-semibold text-gray-600 mb-2">Issues Found:</h4>
          <ul className="list-disc list-inside space-y-1">
            {dataFile.qualityIssues.map((issue: string, index: number) => (
              <div key={index} className="flex items-center space-x-2">
                <span className="text-sm text-red-600">⚠️ {issue}</span>
              </div>
            ))}
          </ul>
        </div>
      )}

      {dataFile.extraData?.quality_metrics && (
        <div className="mt-6">
          <h4 className="text-sm font-semibold text-gray-600 mb-2">Detailed Metrics:</h4>
          <div className="grid grid-cols-2 gap-4">
            {Object.entries(dataFile.extraData.quality_metrics).map(([key, value]) => (
              <div key={key} className="bg-gray-50 p-3 rounded">
                <div className="text-xs text-gray-500">{key.replace(/_/g, ' ').toUpperCase()}</div>
                <div className="text-sm font-medium">{formatMetricValue(value as number, key)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {renderTemporalEvolution()}

      {dataFile.qualityCheckDt && (
        <div className="text-xs text-gray-500 mt-4">
          Last checked: {new Date(dataFile.qualityCheckDt).toLocaleString()}
        </div>
      )}
    </div>
  );
};

export default AudioQualityCard; 