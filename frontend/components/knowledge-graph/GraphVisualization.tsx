'use client';

import { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import type { KnowledgeNode, GraphEdge } from '@/lib/api/knowledge-graph';

interface GraphVisualizationProps {
  nodes: KnowledgeNode[];
  edges: GraphEdge[];
  onNodeClick: (node: KnowledgeNode) => void;
  onNodeQuickComplete?: (node: KnowledgeNode) => void;
  highlightNodeId?: string | null;
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

interface TooltipState {
  x: number;
  y: number;
  node: KnowledgeNode;
}

export function GraphVisualization({
  nodes,
  edges,
  onNodeClick,
  onNodeQuickComplete,
  highlightNodeId,
}: GraphVisualizationProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const minimapRef = useRef<SVGSVGElement>(null);
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);

  const [minimapReady, setMinimapReady] = useState(false);
  const simNodesRef = useRef<(KnowledgeNode & d3.SimulationNodeDatum)[]>([]);
  const zoomRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null);
  // Store minimap projection params so drag handler can convert minimap coords → main coords
  const minimapProjectionRef = useRef({ scale: 1, offX: 0, offY: 0 });

  // Keep callbacks in refs so D3 effect doesn't re-run when they change
  const onNodeClickRef = useRef(onNodeClick);
  const onNodeQuickCompleteRef = useRef(onNodeQuickComplete);
  useEffect(() => {
    onNodeClickRef.current = onNodeClick;
  }, [onNodeClick]);
  useEffect(() => {
    onNodeQuickCompleteRef.current = onNodeQuickComplete;
  }, [onNodeQuickComplete]);

  // Stable structure key — only rebuild D3 when node IDs or edges change
  const structureKey =
    nodes.map((n) => n.id).join(',') + '|' + edges.map((e) => e.source + e.target).join(',');

  // ── Lightweight color update (no simulation restart) ─────────────────────
  useEffect(() => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    nodes.forEach((node) => {
      svg
        .selectAll<SVGCircleElement, unknown>(`circle[data-id="${node.id}"]`)
        .attr('fill', STATUS_COLORS[node.status])
        .attr('stroke', node.id === highlightNodeId ? '#6366f1' : STATUS_STROKE[node.status])
        .attr('stroke-width', node.id === highlightNodeId ? 3 : node.is_unlocked ? 2 : 1)
        .attr('opacity', node.is_unlocked || node.status !== 'not_started' ? 1 : 0.5);
      svg
        .selectAll<SVGTextElement, unknown>(`text[data-check-id="${node.id}"]`)
        .attr('display', node.status === 'completed' ? null : 'none');
    });
  }, [nodes, highlightNodeId]);

  // ── Full D3 rebuild (only when structure changes) ─────────────────────────
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!svgRef.current || nodes.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = svgRef.current.clientWidth || 800;
    const height = svgRef.current.clientHeight || 600;

    const g = svg.append('g');

    // ── Minimap sync ──────────────────────────────────────────────────────────
    const MINI_W = 140;
    const MINI_H = 90;
    let minimapScale = 1;
    let minimapOffsetX = 0;
    let minimapOffsetY = 0;

    const syncMinimap = (transform: d3.ZoomTransform) => {
      if (!minimapRef.current) return;
      const mini = d3.select(minimapRef.current);
      mini.selectAll('*').remove();

      // Draw edges
      mini
        .append('g')
        .selectAll('line')
        .data(simLinks)
        .join('line')
        .attr('stroke', '#94a3b8')
        .attr('stroke-width', 0.5)
        .attr('x1', (d) => ((d.source as SimNode).x ?? 0) * minimapScale + minimapOffsetX)
        .attr('y1', (d) => ((d.source as SimNode).y ?? 0) * minimapScale + minimapOffsetY)
        .attr('x2', (d) => ((d.target as SimNode).x ?? 0) * minimapScale + minimapOffsetX)
        .attr('y2', (d) => ((d.target as SimNode).y ?? 0) * minimapScale + minimapOffsetY);

      // Draw nodes
      mini
        .append('g')
        .selectAll('circle')
        .data(simNodes)
        .join('circle')
        .attr('r', 3)
        .attr('fill', (d) => STATUS_COLORS[d.status])
        .attr('cx', (d) => (d.x ?? 0) * minimapScale + minimapOffsetX)
        .attr('cy', (d) => (d.y ?? 0) * minimapScale + minimapOffsetY);

      // Viewport rect
      const vx = -transform.x / transform.k;
      const vy = -transform.y / transform.k;
      const vw = width / transform.k;
      const vh = height / transform.k;
      mini
        .append('rect')
        .attr('x', vx * minimapScale + minimapOffsetX)
        .attr('y', vy * minimapScale + minimapOffsetY)
        .attr('width', vw * minimapScale)
        .attr('height', vh * minimapScale)
        .attr('fill', 'rgba(99,102,241,0.08)')
        .attr('stroke', '#6366f1')
        .attr('stroke-width', 1)
        .attr('cursor', 'grab')
        .attr('opacity', 0.9);
    };

    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.2, 3])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
        syncMinimap(event.transform);
      });
    svg.call(zoom);
    zoomRef.current = zoom;

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

    const nodeMap = new Map(nodes.map((n) => [n.id, n]));

    type SimNode = KnowledgeNode & d3.SimulationNodeDatum;
    type SimLink = d3.SimulationLinkDatum<SimNode> & { type: string };

    const simNodes: SimNode[] = nodes.map((n) => ({ ...n }));
    simNodesRef.current = simNodes;
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

    const link = g
      .append('g')
      .selectAll('line')
      .data(simLinks)
      .join('line')
      .attr('stroke', (d) => (d.type === 'prerequisite' ? '#94a3b8' : '#cbd5e1'))
      .attr('stroke-width', (d) => (d.type === 'prerequisite' ? 1.5 : 1))
      .attr('stroke-dasharray', (d) => (d.type === 'related' ? '4,4' : null))
      .attr('marker-end', (d) => (d.type === 'prerequisite' ? 'url(#arrow)' : null));

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
      .on('click', (_event, d) => onNodeClickRef.current(d));

    // Main circle — use data-id for lightweight color updates
    node
      .append('circle')
      .attr('data-id', (d) => d.id)
      .attr('r', (d) => 14 + d.difficulty * 2)
      .attr('fill', (d) => STATUS_COLORS[d.status])
      .attr('stroke', (d) => (d.id === highlightNodeId ? '#6366f1' : STATUS_STROKE[d.status]))
      .attr('stroke-width', (d) => (d.id === highlightNodeId ? 3 : d.is_unlocked ? 2 : 1))
      .attr('opacity', (d) => (d.is_unlocked || d.status !== 'not_started' ? 1 : 0.5));

    // Highlight ring
    node
      .filter((d) => d.id === highlightNodeId)
      .append('circle')
      .attr('r', (d) => 20 + d.difficulty * 2)
      .attr('fill', 'none')
      .attr('stroke', '#6366f1')
      .attr('stroke-width', 1.5)
      .attr('stroke-dasharray', '4,3')
      .attr('opacity', 0.7);

    // Lock indicator — white circle badge + Lucide lock path
    const lockGroup = node
      .filter((d) => !d.is_unlocked && d.status === 'not_started')
      .append('g')
      .attr('transform', (d) => `translate(${-(8 + d.difficulty)}, ${-(8 + d.difficulty)})`);

    lockGroup
      .append('circle')
      .attr('r', 7)
      .attr('fill', 'white')
      .attr('stroke', '#94a3b8')
      .attr('stroke-width', 1);

    lockGroup
      .append('path')
      .attr(
        'd',
        'M5 11V7a4 4 0 0 1 8 0v4M3 11h12a1 1 0 0 1 1 1v6a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1v-6a1 1 0 0 1 1-1z'
      )
      .attr('fill', 'none')
      .attr('stroke', '#475569')
      .attr('stroke-width', 2)
      .attr('stroke-linecap', 'round')
      // viewBox 24×24, scale 0.5 → 12×12; visual center of lock ~(9,12) → center in circle
      .attr('transform', 'scale(0.5) translate(-9, -12)');

    // Completed checkmark — always rendered, visibility controlled by lightweight effect
    node
      .append('text')
      .attr('data-check-id', (d) => d.id)
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'central')
      .attr('fill', 'white')
      .attr('font-weight', 'bold')
      .attr('font-size', '13px')
      .attr('display', (d) => (d.status === 'completed' ? null : 'none'))
      .text('✓');

    // Quick-complete button (✓ on hover for unlocked, non-completed nodes)
    if (onNodeQuickCompleteRef.current) {
      const quickBtn = node
        .filter((d) => d.is_unlocked && d.status !== 'completed')
        .append('g')
        .attr('class', 'quick-complete')
        .attr('opacity', 0)
        .attr('cursor', 'pointer');

      quickBtn
        .append('circle')
        .attr('r', 9)
        .attr('cx', (d) => 12 + d.difficulty * 2)
        .attr('cy', (d) => -(12 + d.difficulty * 2))
        .attr('fill', '#22c55e')
        .attr('stroke', 'white')
        .attr('stroke-width', 1.5);

      quickBtn
        .append('text')
        .attr('x', (d) => 12 + d.difficulty * 2)
        .attr('y', (d) => -(12 + d.difficulty * 2))
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'central')
        .attr('fill', 'white')
        .attr('font-size', '10px')
        .attr('font-weight', 'bold')
        .attr('pointer-events', 'none')
        .text('✓');

      quickBtn.on('click', (event, d) => {
        event.stopPropagation();
        onNodeQuickCompleteRef.current?.(d);
      });

      node
        .on('mouseenter.quickbtn', function () {
          d3.select(this).select('.quick-complete').attr('opacity', 1);
        })
        .on('mouseleave.quickbtn', function () {
          d3.select(this).select('.quick-complete').attr('opacity', 0);
        });
    }

    // Labels
    node
      .append('text')
      .attr('data-label-id', (d) => d.id)
      .attr('dy', (d) => 20 + d.difficulty * 2)
      .attr('text-anchor', 'middle')
      .attr('font-size', '11px')
      .attr('fill', 'currentColor')
      .attr('class', 'select-none')
      .text((d) =>
        d.display_name.length > 18 ? d.display_name.slice(0, 16) + '…' : d.display_name
      );

    // React-controlled tooltip (replaces DOM-appended div)
    node
      .on('mouseenter.tooltip', (event, d) => {
        setTooltip({ x: event.clientX, y: event.clientY, node: d });
      })
      .on('mousemove.tooltip', (event) => {
        setTooltip((prev) => (prev ? { ...prev, x: event.clientX, y: event.clientY } : null));
      })
      .on('mouseleave.tooltip', () => setTooltip(null));

    simulation.on('tick', () => {
      link
        .attr('x1', (d) => (d.source as SimNode).x ?? 0)
        .attr('y1', (d) => (d.source as SimNode).y ?? 0)
        .attr('x2', (d) => (d.target as SimNode).x ?? 0)
        .attr('y2', (d) => (d.target as SimNode).y ?? 0);
      node.attr('transform', (d) => `translate(${d.x ?? 0},${d.y ?? 0})`);
    });

    // Compute minimap scale after simulation settles
    simulation.on('end', () => {
      const xs = simNodes.map((n) => n.x ?? 0);
      const ys = simNodes.map((n) => n.y ?? 0);
      const minX = Math.min(...xs);
      const maxX = Math.max(...xs);
      const minY = Math.min(...ys);
      const maxY = Math.max(...ys);
      const graphW = maxX - minX || 1;
      const graphH = maxY - minY || 1;
      minimapScale = Math.min((MINI_W - 16) / graphW, (MINI_H - 16) / graphH);
      minimapOffsetX = (MINI_W - graphW * minimapScale) / 2 - minX * minimapScale;
      minimapOffsetY = (MINI_H - graphH * minimapScale) / 2 - minY * minimapScale;
      minimapProjectionRef.current = {
        scale: minimapScale,
        offX: minimapOffsetX,
        offY: minimapOffsetY,
      };
      syncMinimap(d3.zoomTransform(svgRef.current!));
      setMinimapReady(true);
    });

    return () => {
      simulation.stop();
      setTooltip(null);
      setMinimapReady(false);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [structureKey]);

  // Re-sync minimap once its SVG mounts (after minimapReady flips true)
  useEffect(() => {
    if (!minimapReady || !minimapRef.current || !svgRef.current) return;
    // Trigger a zoom event to repaint minimap with current transform
    const currentTransform = d3.zoomTransform(svgRef.current);
    const mini = d3.select(minimapRef.current);
    mini.selectAll('*').remove();
    // Re-draw by dispatching a synthetic zoom — reuse simNodesRef
    const nodes = simNodesRef.current;
    if (!nodes.length) return;
    const xs = nodes.map((n) => n.x ?? 0);
    const ys = nodes.map((n) => n.y ?? 0);
    const minX = Math.min(...xs),
      maxX = Math.max(...xs);
    const minY = Math.min(...ys),
      maxY = Math.max(...ys);
    const MINI_W = 140,
      MINI_H = 90;
    const graphW = maxX - minX || 1,
      graphH = maxY - minY || 1;
    const scale = Math.min((MINI_W - 16) / graphW, (MINI_H - 16) / graphH);
    const offX = (MINI_W - graphW * scale) / 2 - minX * scale;
    const offY = (MINI_H - graphH * scale) / 2 - minY * scale;
    minimapProjectionRef.current = { scale, offX, offY };
    mini
      .append('g')
      .selectAll('circle')
      .data(nodes)
      .join('circle')
      .attr('r', 3)
      .attr('fill', (d) => STATUS_COLORS[(d as KnowledgeNode).status])
      .attr('cx', (d) => (d.x ?? 0) * scale + offX)
      .attr('cy', (d) => (d.y ?? 0) * scale + offY);
    const vx = -currentTransform.x / currentTransform.k;
    const vy = -currentTransform.y / currentTransform.k;
    mini
      .append('rect')
      .attr('class', 'minimap-viewport')
      .attr('x', vx * scale + offX)
      .attr('y', vy * scale + offY)
      .attr('width', ((svgRef.current.clientWidth || 800) / currentTransform.k) * scale)
      .attr('height', ((svgRef.current.clientHeight || 600) / currentTransform.k) * scale)
      .attr('fill', 'rgba(99,102,241,0.08)')
      .attr('stroke', '#6366f1')
      .attr('stroke-width', 1)
      .attr('cursor', 'grab')
      .attr('opacity', 0.9);

    // Drag on minimap → pan main view
    mini.call(
      d3.drag<SVGSVGElement, unknown>().on('drag', (event) => {
        if (!svgRef.current || !zoomRef.current) return;
        const { scale: ms, offX: mox, offY: moy } = minimapProjectionRef.current;
        // Convert minimap delta to graph-space delta, then to screen-space
        const currentT = d3.zoomTransform(svgRef.current);
        const dx = (event.dx / ms) * currentT.k;
        const dy = (event.dy / ms) * currentT.k;
        d3.select(svgRef.current).call(zoomRef.current.translateBy, -dx, -dy);
      })
    );
  }, [minimapReady]);
  useEffect(() => {
    if (!highlightNodeId || !svgRef.current || !zoomRef.current) return;
    const target = simNodesRef.current.find((n) => n.id === highlightNodeId);
    if (
      target?.x === null ||
      target?.x === undefined ||
      target?.y === null ||
      target?.y === undefined
    )
      return;
    const svg = d3.select(svgRef.current);
    const w = svgRef.current.clientWidth || 800;
    const h = svgRef.current.clientHeight || 600;
    const scale = 1.5;
    svg
      .transition()
      .duration(600)
      .call(
        zoomRef.current.transform,
        d3.zoomIdentity.translate(w / 2 - scale * target.x, h / 2 - scale * target.y).scale(scale)
      );
  }, [highlightNodeId]);

  return (
    <div className="relative w-full h-full">
      <svg
        ref={svgRef}
        className="w-full h-full"
        style={{ minHeight: '500px' }}
        aria-label="Knowledge graph visualization"
      />

      {/* Minimap — only shown after simulation settles */}
      {minimapReady && (
        <div className="absolute bottom-4 right-4 rounded-lg border bg-background/90 backdrop-blur overflow-hidden shadow-sm">
          <svg ref={minimapRef} width={140} height={90} aria-hidden="true" />
        </div>
      )}

      {/* React-controlled tooltip */}
      {tooltip && (
        <div
          className="fixed z-[9999] pointer-events-none rounded-md px-3 py-2 text-xs text-white shadow-lg"
          style={{
            background: 'rgba(0,0,0,0.85)',
            left: tooltip.x + 12,
            top: tooltip.y - 28,
            maxWidth: 220,
          }}
        >
          <strong>{tooltip.node.display_name}</strong>
          <br />
          Difficulty: {tooltip.node.difficulty}/5
          <br />
          Est. {tooltip.node.estimated_hours}h · {tooltip.node.status.replace('_', ' ')}
        </div>
      )}
    </div>
  );
}
