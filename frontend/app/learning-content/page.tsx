import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { BookOpen, Clock, Star, TrendingUp, Filter } from 'lucide-react';

interface Article {
  id: string;
  title: string;
  url: string;
  published_at: string;
  ai_summary: string;
  tinkering_index: number;
}

interface Classification {
  content_type: string;
  difficulty_level: number;
  learning_value_score: number;
  educational_features: {
    has_code_examples: boolean;
    has_step_by_step: boolean;
    estimated_reading_time: number;
  };
}

interface LearningArticle {
  article: Article;
  classification: Classification;
  score: number;
}

export default function LearningContentPage() {
  const [articles, setArticles] = useState<LearningArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedType, setSelectedType] = useState<string>('all');

  useEffect(() => {
    fetchLearningContent();
  }, [selectedType]);

  const fetchLearningContent = async () => {
    try {
      setLoading(true);
      const contentTypes =
        selectedType === 'all' ? ['tutorial', 'guide', 'project', 'reference'] : [selectedType];

      const params = new URLSearchParams({
        content_types: contentTypes.join(','),
        limit: '20',
      });

      const response = await fetch(`/api/learning-content-simple/articles?${params}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setArticles(data.recommendations || []);
      }
    } catch (error) {
      console.error('Failed to fetch learning content:', error);
    } finally {
      setLoading(false);
    }
  };

  const getDifficultyLabel = (level: number) => {
    const labels = { 1: 'Beginner', 2: 'Intermediate', 3: 'Advanced', 4: 'Expert' };
    return labels[level as keyof typeof labels] || 'Unknown';
  };

  const getTypeColor = (type: string) => {
    const colors = {
      tutorial: 'bg-blue-100 text-blue-800',
      guide: 'bg-green-100 text-green-800',
      project: 'bg-purple-100 text-purple-800',
      reference: 'bg-gray-100 text-gray-800',
      news: 'bg-orange-100 text-orange-800',
    };
    return colors[type as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Learning Content</h1>
        <p className="text-gray-600">
          Discover curated educational content tailored to your learning journey
        </p>
      </div>

      <Tabs value={selectedType} onValueChange={setSelectedType} className="mb-6">
        <TabsList>
          <TabsTrigger value="all">All Content</TabsTrigger>
          <TabsTrigger value="tutorial">Tutorials</TabsTrigger>
          <TabsTrigger value="guide">Guides</TabsTrigger>
          <TabsTrigger value="project">Projects</TabsTrigger>
          <TabsTrigger value="reference">Reference</TabsTrigger>
        </TabsList>
      </Tabs>

      {articles.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <BookOpen className="h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Learning Content Available</h3>
            <p className="text-gray-600 text-center mb-4">
              We're still processing articles and building your personalized learning
              recommendations.
            </p>
            <Button onClick={fetchLearningContent}>Refresh Content</Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {articles.map((item) => (
            <Card
              key={item.article.id}
              className="hover:shadow-lg transition-shadow cursor-pointer"
            >
              <CardHeader>
                <div className="flex items-start justify-between mb-2">
                  <Badge className={getTypeColor(item.classification.content_type)}>
                    {item.classification.content_type}
                  </Badge>
                  <div className="flex items-center text-sm text-gray-500">
                    <Star className="h-4 w-4 mr-1" />
                    {item.classification.learning_value_score.toFixed(1)}
                  </div>
                </div>
                <CardTitle className="text-lg leading-tight">
                  <a
                    href={item.article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-blue-600 transition-colors"
                  >
                    {item.article.title}
                  </a>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
                  <div className="flex items-center">
                    <TrendingUp className="h-4 w-4 mr-1" />
                    {getDifficultyLabel(item.classification.difficulty_level)}
                  </div>
                  <div className="flex items-center">
                    <Clock className="h-4 w-4 mr-1" />
                    {item.classification.educational_features.estimated_reading_time}min
                  </div>
                </div>

                {item.article.ai_summary && (
                  <p className="text-sm text-gray-700 mb-3 line-clamp-3">
                    {item.article.ai_summary}
                  </p>
                )}

                <div className="flex flex-wrap gap-2 mb-3">
                  {item.classification.educational_features.has_code_examples && (
                    <Badge variant="outline" className="text-xs">
                      Code Examples
                    </Badge>
                  )}
                  {item.classification.educational_features.has_step_by_step && (
                    <Badge variant="outline" className="text-xs">
                      Step-by-Step
                    </Badge>
                  )}
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">
                    {new Date(item.article.published_at).toLocaleDateString()}
                  </span>
                  <Button size="sm" variant="outline" asChild>
                    <a href={item.article.url} target="_blank" rel="noopener noreferrer">
                      Read Article
                    </a>
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
