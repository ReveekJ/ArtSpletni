export interface LayoutNode {
  id: number;
  dependsOn: number[];
}

export interface Position {
  x: number;
  y: number;
}

const LAYER_SPACING_X = 280;
const NODE_SPACING_Y = 120;
const BASE_Y = 100;
const BASE_X = 50;

export function computeDagLayout(nodes: LayoutNode[]): Record<number, Position> {
  const nodeMap = new Map<number, LayoutNode>();
  for (const node of nodes) {
    nodeMap.set(node.id, node);
  }

  const layerCache = new Map<number, number>();

  const getLayer = (id: number): number => {
    if (layerCache.has(id)) {
      return layerCache.get(id)!;
    }
    const node = nodeMap.get(id);
    if (!node || node.dependsOn.length === 0) {
      layerCache.set(id, 0);
      return 0;
    }
    const maxDepLayer = Math.max(...node.dependsOn.map((depId) => getLayer(depId)));
    const layer = maxDepLayer + 1;
    layerCache.set(id, layer);
    return layer;
  };

  const layers = new Map<number, number[]>();
  for (const node of nodes) {
    const layer = getLayer(node.id);
    if (!layers.has(layer)) {
      layers.set(layer, []);
    }
    layers.get(layer)!.push(node.id);
  }

  const positions: Record<number, Position> = {};
  const sortedLayerKeys = [...layers.keys()].sort((a, b) => a - b);

  for (const layerIndex of sortedLayerKeys) {
    const layerNodes = layers.get(layerIndex)!;
    const layerHeight = (layerNodes.length - 1) * NODE_SPACING_Y;
    const startY = BASE_Y - layerHeight / 2;

    layerNodes.forEach((nodeId, indexInLayer) => {
      positions[nodeId] = {
        x: BASE_X + layerIndex * LAYER_SPACING_X,
        y: startY + indexInLayer * NODE_SPACING_Y,
      };
    });
  }

  return positions;
}
