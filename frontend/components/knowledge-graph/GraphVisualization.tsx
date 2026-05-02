'use client';

import { useEffect, useRef, useCallback } from 'react';
import * as d3 from 'd3';
import type { KnowledgeNode, GraphEdge } from '@/lib/api/knowledge-graph';

interface GraphVisualizationProps {
  nodes: KnowledgeNode[];
  edges: GraphEdge[];
  onNodeClick: (node: KnowledgeNode) => void;
}

const STATUS_COLORS = {
  completed: '#22c55e',
  in_progress: '#f59e0b',
  not_started: '#94a3b8',
};

const STATUS_STROKE = {
  completed: '#16a34a',
  in_progress: '#d97706',
  not_started: '#64748b',
};

export function GraphVisualization({ nodes, edges, onNodeClick }: GraphVisualizationProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const handleNodeClick = useCallback(onNodeClick, [onNodeClick]);

  useEffect(() => {
    if (!svgRef.current || nodes.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = svgRef.current.clientWidth || 800;
    const height = svgRef.current.clientHeight || 600;

    // Zoom container
    const g = svg.append('g');
    svg.call(
      d3
        .zoom<SVGSVGElement, unknown>()
        .scaleExtent([0.2, 3])
        .on('zoom', (event) => g.attr('transform', event.transform))
    );

    // Arrow marker
    svg
      .append('defs')
      .append('marker')
      .attr('id', 'arrow')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 20)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#94a3b8');

    // Build node map
    const nodeMap = new Map(nodes.map((n) => [n.id, n]));

    // D3 simulation nodes/links
    type SimNode = KnowledgeNode & d3.SimulationNodeDatum;
    type SimLink = d3.SimulationLinkDatum<SimNode> & { type: string };

    const simNodes: SimNode[] = nodes.map((n) => ({ ...n }));
    const simLinks: SimLink[] = edges
      .filter((e) => nodeMap.has(e.source) && nodeMap.has(e.target))
      .map((e) => ({ source: e.source, target: e.target, type: e.type }));

    const simulation = d3
      .forceSimulation<SimNode>(simNodes)
      .force(
        'link',
        d3
          .forceLink<SimNode, SimLink>(simLinks)
          .id((d) => d.id)
          .distance(120)
      )
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide(40));

    // Edges
    const link = g
      .append('g')
      .selectAll('line')
      .data(simLinks)
      .join('line')
      .attr('stroke', (d) => (d.type === 'prerequisite' ? '#94a3b8' : '#cbd5e1'))
      .attr('stroke-width', (d) => (d.type === 'prerequisite' ? 1.5 : 1))
      .attr('stroke-dasharray', (d) => (d.type === 'related' ? '4,4' : null))
      .attr('marker-end', (d) => (d.type === 'prerequisite' ? 'url(#arrow)' : null));

    // Node groups
    const node = g
      .append('g')
      .selectAll('g')
      .data(simNodes)
      .join('g')
      .attr('cursor', 'pointer')
      .call(
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        d3
          .drag<SVGGElement, SimNode>()
          .on('start', (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on('drag', (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on('end', (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          }) as any
      )
      .on('click', (_event, d) => handleNodeClick(d));

    // Node circles
    node
      .append('circle')
      .attr('r', (d) => 14 + d.difficulty * 2)
      .attr('fill', (d) => STATUS_COLORS[d.status])
      .attr('stroke', (d) => STATUS_STROKE[d.status])
      .attr('stroke-width', (d) => (d.is_unlocked ? 2 : 1))
      .attr('opacity', (d) => (d.is_unlocked || d.status !== 'not_started' ? 1 : 0.5));

    // Lock icon for locked nodes
    node
      .filter((d) => !d.is_unlocked && d.status === 'not_started')
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'central')
      .attr('font-size', '12px')
      .text('🔒');

    // Checkmark for completed
    node
      .filter((d) => d.status === 'completed')
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'central')
      .attr('font-size', '14px')
      .text('✓')
      .attr('fill', 'white')
      .attr('font-weight', 'bold');

    // Labels
    node
      .append('text')
      .attr('dy', (d) => 20 + d.difficulty * 2)
      .attr('text-anchor', 'middle')
      .attr('font-size', '11px')
      .attr('fill', 'currentColor')
      .attr('class', 'select-none')
      .text((d) =>
        d.display_name.length > 18 ? d.display_name.slice(0, 16) + '…' : d.display_name
      );

    // Tooltip
    const tooltip = d3
      .select('body')
      .append('div')
      .attr('class', 'kg-tooltip')
      .style('position', 'fixed')
      .style('background', 'rgba(0,0,0,0.85)')
      .style('color', 'white')
      .style('padding', '8px 12px')
      .style('border-radius', '6px')
      .style('font-size', '12px')
      .style('pointer-events', 'none')
      .style('opacity', 0)
      .style('z-index', '9999')
      .style('max-width', '220px');

    node
      .on('mouseenter', (event, d) => {
        tooltip
          .style('opacity', 1)
          .html(
            `<strong>${d.display_name}</strong><br/>` +
              `Difficulty: ${'★'.repeat(d.difficulty)}${'☆'.repeat(5 - d.difficulty)}<br/>` +
              `Est. ${d.estimated_hours}h · ${d.status.replace('_', ' ')}`
          );
      })
      .on('mousemove', (event) => {
        tooltip.style('left', event.clientX + 12 + 'px').style('top', event.clientY - 28 + 'px');
      })
      .on('mouseleave', () => tooltip.style('opacity', 0));

    simulation.on('tick', () => {
      link
        .attr('x1', (d) => (d.source as SimNode).x ?? 0)
        .attr('y1', (d) => (d.source as SimNode).y ?? 0)
        .attr('x2', (d) => (d.target as SimNode).x ?? 0)
        .attr('y2', (d) => (d.target as SimNode).y ?? 0);

      node.attr('transform', (d) => `translate(${d.x ?? 0},${d.y ?? 0})`);
    });

    return () => {
      simulation.stop();
      tooltip.remove();
    };
  }, [nodes, edges, handleNodeClick]);

  return (
    <svg
      ref={svgRef}
      className="w-full h-full"
      style={{ minHeight: '500px' }}
      aria-label="Knowledge graph visualization"
    />
  );
}
