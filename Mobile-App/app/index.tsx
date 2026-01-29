// import React, { useState, useEffect, useMemo } from 'react';
// import {
//   View,
//   Text,
//   TextInput,
//   ScrollView,
//   TouchableOpacity,
//   StyleSheet,
//   Dimensions,
//   useColorScheme,
//   Platform,
//   StatusBar,
//   Alert,
// } from 'react-native';
// import AsyncStorage from '@react-native-async-storage/async-storage';
// import Plotly from 'react-native-plotly';
// import * as math from 'mathjs';

// const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');
// const GRAPH_WIDTH = SCREEN_WIDTH - 40;
// const GRAPH_HEIGHT = 300;

// // Types
// interface Point {
//   x: number;
//   y: number;
// }

// interface AsymptoteOblique {
//   m: number;
//   b: number;
// }

// interface AnalysisResults {
//   criticalPoints: Point[];
//   roots: number[];
//   inflectionPoints: Point[];
//   undefinedValues: Point[];
//   verticalAsymptotes: number[];
//   horizontalAsymptote: number | null;
//   obliqueAsymptote: AsymptoteOblique | null;
// }

// // Math Analyzer Class - Keep this EXACTLY the same as HTML version
// class MathAnalyzer {
//   funcStr: string;
//   xRange: [number, number];
//   numPoints: number;
//   node: any;
//   func: any;
//   derivNode: any;
//   deriv: any;
//   secondDerivNode: any;
//   secondDeriv: any;
//   errors: string[];

//   constructor(funcStr: string, xRange: [number, number], numPoints = 1000) {
//     this.funcStr = this.normalizeFunction(funcStr);
//     this.xRange = xRange;
//     this.numPoints = numPoints;
//     this.errors = [];

//     try {
//       this.node = math.parse(this.funcStr);
//       this.func = this.node.compile();

//       // Keep original for undefined detection
//       this.funcOriginal = this.func;

//       this.derivNode = math.derivative(this.node, 'x');
//       this.deriv = this.derivNode.compile();
//       this.secondDerivNode = math.derivative(this.derivNode, 'x');
//       this.secondDeriv = this.secondDerivNode.compile();
//     } catch (e: any) {
//       this.errors.push(`Parse error: ${e.message}`);
//     }
//   }

//   normalizeFunction(input: string): string {
//     let normalized = input;
//     normalized = normalized.replace(/²/g, '^2');
//     normalized = normalized.replace(/³/g, '^3');
//     normalized = normalized.replace(/⁴/g, '^4');
//     normalized = normalized.replace(/⁵/g, '^5');
//     normalized = normalized.replace(/⁶/g, '^6');
//     normalized = normalized.replace(/\*\*/g, '^');

//     const openParen = (normalized.match(/\(/g) || []).length;
//     const closeParen = (normalized.match(/\)/g) || []).length;
//     if (openParen > closeParen) {
//       normalized += ')'.repeat(openParen - closeParen);
//     }

//     const openSquare = (normalized.match(/\[/g) || []).length;
//     const closeSquare = (normalized.match(/\]/g) || []).length;
//     if (openSquare > closeSquare) {
//       normalized += ']'.repeat(openSquare - closeSquare);
//     }

//     normalized = normalized.replace(/sqrt/gi, 'sqrt');
//     normalized = normalized.replace(/abs/gi, 'abs');

//     return normalized;
//   }

//   evaluate(x: number): number {
//     try {
//       const result = this.func.evaluate({ x });
//       return isFinite(result) ? result : NaN;
//     } catch {
//       return NaN;
//     }
//   }

//   evaluateDerivative(x: number): number {
//     try {
//       const result = this.deriv.evaluate({ x });
//       return isFinite(result) ? result : NaN;
//     } catch {
//       return NaN;
//     }
//   }

//   evaluateSecondDerivative(x: number): number {
//     try {
//       const result = this.secondDeriv.evaluate({ x });
//       return isFinite(result) ? result : NaN;
//     } catch {
//       return NaN;
//     }
//   }

//   evaluateDerivativeLimit(x: number, direction: 'left' | 'right' | 'both' = 'both'): number {
//     const h = 1e-7;
//     if (direction === 'left') {
//       const f_x = this.evaluate(x);
//       const f_x_h = this.evaluate(x - h);
//       return (f_x - f_x_h) / h;
//     } else if (direction === 'right') {
//       const f_x = this.evaluate(x);
//       const f_x_h = this.evaluate(x + h);
//       return (f_x_h - f_x) / h;
//     } else {
//       const f_x_h = this.evaluate(x + h);
//       const f_x_h_neg = this.evaluate(x - h);
//       return (f_x_h - f_x_h_neg) / (2 * h);
//     }
//   }

//   generatePoints(): { x: number[], y: number[] } {
//     const [xMin, xMax] = this.xRange;
//     const step = (xMax - xMin) / this.numPoints;
//     const x: number[] = [];
//     const y: number[] = [];

//     for (let i = 0; i <= this.numPoints; i++) {
//       const xVal = xMin + i * step;
//       const yVal = this.evaluate(xVal);
//       x.push(xVal);
//       y.push(yVal);
//     }

//     return { x, y };
//   }

//   generateDerivativePoints(): { x: number[], y: number[] } {
//     const [xMin, xMax] = this.xRange;
//     const step = (xMax - xMin) / this.numPoints;
//     const x: number[] = [];
//     const y: number[] = [];

//     for (let i = 0; i <= this.numPoints; i++) {
//       const xVal = xMin + i * step;
//       const yVal = this.evaluateDerivative(xVal);
//       x.push(xVal);
//       y.push(yVal);
//     }

//     return { x, y };
//   }

//   generateSecondDerivativePoints(): { x: number[], y: number[] } {
//     const [xMin, xMax] = this.xRange;
//     const step = (xMax - xMin) / this.numPoints;
//     const x: number[] = [];
//     const y: number[] = [];

//     for (let i = 0; i <= this.numPoints; i++) {
//       const xVal = xMin + i * step;
//       const yVal = this.evaluateSecondDerivative(xVal);
//       x.push(xVal);
//       y.push(yVal);
//     }

//     return { x, y };
//   }

//   bisectionMethod(a: number, b: number, tolerance = 0.0001, maxIter = 50): number | null {
//     let fa = this.evaluate(a);
//     let fb = this.evaluate(b);

//     if (fa * fb > 0) return null;

//     for (let i = 0; i < maxIter; i++) {
//       const c = (a + b) / 2;
//       const fc = this.evaluate(c);

//       if (Math.abs(fc) < tolerance || (b - a) / 2 < tolerance) {
//         return c;
//       }

//       if (fa * fc < 0) {
//         b = c;
//         fb = fc;
//       } else {
//         a = c;
//         fa = fc;
//       }
//     }

//     return (a + b) / 2;
//   }

//   findRoots(): number[] {
//     const [xMin, xMax] = this.xRange;
//     const step = (xMax - xMin) / 1000;
//     const roots: number[] = [];
//     let prevY = this.evaluate(xMin);

//     for (let x = xMin + step; x <= xMax; x += step) {
//       const y = this.evaluate(x);
//       if (!isNaN(y) && !isNaN(prevY)) {
//         if (prevY * y < 0 || Math.abs(y) < 0.001) {
//           const root = this.bisectionMethod(x - step, x);
//           if (root !== null && !roots.some((r) => Math.abs(r - root) < 0.01)) {
//             roots.push(root);
//           }
//         }
//       }
//       prevY = y;
//     }

//     return roots;
//   }

//   bisectionDerivative(a: number, b: number, tolerance = 0.0001, maxIter = 50): number | null {
//     let fa = this.evaluateDerivative(a);
//     let fb = this.evaluateDerivative(b);

//     if (fa * fb > 0) return null;

//     for (let i = 0; i < maxIter; i++) {
//       const c = (a + b) / 2;
//       const fc = this.evaluateDerivative(c);

//       if (Math.abs(fc) < tolerance || (b - a) / 2 < tolerance) {
//         return c;
//       }

//       if (fa * fc < 0) {
//         b = c;
//         fb = fc;
//       } else {
//         a = c;
//         fa = fc;
//       }
//     }

//     return (a + b) / 2;
//   }

//   findCriticalPoints(): Point[] {
//     const [xMin, xMax] = this.xRange;
//     const step = (xMax - xMin) / 1000;
//     const criticalPoints: Point[] = [];
//     let prevDy = this.evaluateDerivative(xMin);

//     for (let x = xMin + step; x <= xMax; x += step) {
//       const dy = this.evaluateDerivative(x);
//       if (!isNaN(dy) && !isNaN(prevDy)) {
//         if (prevDy * dy < 0 || Math.abs(dy) < 0.001) {
//           const critX = this.bisectionDerivative(x - step, x);
//           if (critX !== null && !criticalPoints.some((p) => Math.abs(p.x - critX) < 0.01)) {
//             const critY = this.evaluate(critX);
//             if (!isNaN(critY)) {
//               criticalPoints.push({ x: critX, y: critY });
//             }
//           }
//         }
//       }
//       prevDy = dy;
//     }

//     return criticalPoints;
//   }

//   bisectionSecondDerivative(a: number, b: number, tolerance = 0.0001, maxIter = 50): number | null {
//     let fa = this.evaluateSecondDerivative(a);
//     let fb = this.evaluateSecondDerivative(b);

//     if (fa * fb > 0) return null;

//     for (let i = 0; i < maxIter; i++) {
//       const c = (a + b) / 2;
//       const fc = this.evaluateSecondDerivative(c);

//       if (Math.abs(fc) < tolerance || (b - a) / 2 < tolerance) {
//         return c;
//       }

//       if (fa * fc < 0) {
//         b = c;
//         fb = fc;
//       } else {
//         a = c;
//         fa = fc;
//       }
//     }

//     return (a + b) / 2;
//   }

//   findInflectionPoints(): Point[] {
//     const [xMin, xMax] = this.xRange;
//     const step = (xMax - xMin) / 1000;
//     const inflectionPoints: Point[] = [];
//     let prevDdy = this.evaluateSecondDerivative(xMin);

//     for (let x = xMin + step; x <= xMax; x += step) {
//       const ddy = this.evaluateSecondDerivative(x);
//       if (!isNaN(ddy) && !isNaN(prevDdy)) {
//         if (prevDdy * ddy < 0 || Math.abs(ddy) < 0.001) {
//           const inflX = this.bisectionSecondDerivative(x - step, x);
//           if (inflX !== null && !inflectionPoints.some((p) => Math.abs(p.x - inflX) < 0.01)) {
//             const inflY = this.evaluate(inflX);
//             if (!isNaN(inflY)) {
//               inflectionPoints.push({ x: inflX, y: inflY });
//             }
//           }
//         }
//       }
//       prevDdy = ddy;
//     }

//     return inflectionPoints;
//   }

//   findUndefinedValues(): Point[] {
//     const [xMin, xMax] = this.xRange;
//     const undefined: Point[] = [];

//     if (!this.funcStr.includes('/')) {
//       return [];
//     }

//     const step = (xMax - xMin) / 1000;

//     for (let x = xMin; x <= xMax; x += step) {
//       const y = this.evaluate(x);

//       if (isNaN(y) || !isFinite(y)) {
//         const h = 0.0001;
//         const leftVal = this.evaluate(x - h);
//         const rightVal = this.evaluate(x + h);

//         if (isFinite(leftVal) && isFinite(rightVal) && Math.abs(leftVal - rightVal) < 0.01) {
//           const limitVal = (leftVal + rightVal) / 2;

//           if (!undefined.some((p) => Math.abs(p.x - x) < step * 2)) {
//             undefined.push({ x, y: limitVal });
//           }
//         }
//       }
//     }

//     return undefined;
//   }

//   findVerticalAsymptotes(): number[] {
//     const [xMin, xMax] = this.xRange;
//     const step = (xMax - xMin) / 1000;
//     const asymptotes: number[] = [];
//     let prevY = this.evaluate(xMin);

//     for (let x = xMin + step; x <= xMax; x += step) {
//       const y = this.evaluate(x);

//       if ((isFinite(prevY) && !isFinite(y)) || (!isFinite(prevY) && isFinite(y))) {
//         const h = 0.0001;
//         const leftVal = this.evaluate(x - h);
//         const rightVal = this.evaluate(x + h);

//         if (!isFinite(leftVal) || !isFinite(rightVal) || Math.abs(leftVal - rightVal) > 10) {
//           if (!asymptotes.some((a) => Math.abs(a - x) < step * 2)) {
//             asymptotes.push(x);
//           }
//         }
//       } else if (isFinite(prevY) && isFinite(y) && Math.abs(y - prevY) > 1000) {
//         if (!asymptotes.some((a) => Math.abs(a - x) < step * 2)) {
//           asymptotes.push(x);
//         }
//       }

//       prevY = y;
//     }

//     return asymptotes;
//   }

//   findHorizontalAsymptote(): number | null {
//     const farRight = this.evaluate(this.xRange[1] * 10);
//     const farLeft = this.evaluate(this.xRange[0] * 10);

//     if (isFinite(farRight) && isFinite(farLeft) && Math.abs(farRight - farLeft) < 0.1) {
//       return (farRight + farLeft) / 2;
//     }

//     return null;
//   }

//   findObliqueAsymptote(): AsymptoteOblique | null {
//     if (this.findHorizontalAsymptote() !== null) {
//       return null;
//     }

//     const [xMin, xMax] = this.xRange;
//     const xLarge = Math.max(Math.abs(xMin), Math.abs(xMax)) * 10;

//     const f_pos = this.evaluate(xLarge);
//     const f_neg = this.evaluate(-xLarge);

//     if (!isFinite(f_pos) || !isFinite(f_neg)) {
//       return null;
//     }

//     const m_pos = f_pos / xLarge;
//     const m_neg = f_neg / -xLarge;

//     if (!isFinite(m_pos) || !isFinite(m_neg) || Math.abs(m_pos) < 0.001 || Math.abs(m_neg) < 0.001) {
//       return null;
//     }

//     if (Math.abs(m_pos - m_neg) > 0.1) {
//       return null;
//     }

//     const m = (m_pos + m_neg) / 2;
//     const b_pos = f_pos - m * xLarge;
//     const b_neg = f_neg - m * -xLarge;

//     if (!isFinite(b_pos) || !isFinite(b_neg)) {
//       return null;
//     }

//     if (Math.abs(b_pos - b_neg) > 1) {
//       return null;
//     }

//     const b = (b_pos + b_neg) / 2;

//     return { m, b };
//   }
// }

// // Checkbox Component
// function CheckboxItem({ 
//   label, 
//   checked, 
//   onToggle, 
//   colors, 
//   color 
// }: { 
//   label: string; 
//   checked: boolean; 
//   onToggle: (val: boolean) => void; 
//   colors: any; 
//   color: string;
// }) {
//   return (
//     <TouchableOpacity
//       style={[styles.controlItem, { backgroundColor: colors.bgSecondary, borderColor: colors.borderColor }]}
//       onPress={() => onToggle(!checked)}
//     >
//       <View style={[styles.checkbox, { borderColor: colors.borderColor, backgroundColor: checked ? colors.accentPrimary : 'transparent' }]}>
//         {checked && <Text style={styles.checkmark}>✓</Text>}
//       </View>
//       <Text style={[styles.controlLabel, { color: colors.textPrimary }]}>{label}</Text>
//       <View style={[styles.colorIndicator, { backgroundColor: color }]} />
//     </TouchableOpacity>
//   );
// }

// // Analysis Card Component
// function AnalysisCard({ 
//   title, 
//   content, 
//   colors 
// }: { 
//   title: string; 
//   content: string; 
//   colors: any;
// }) {
//   return (
//     <View style={[styles.analysisCard, { backgroundColor: colors.bgSecondary, borderLeftColor: colors.accentPrimary }]}>
//       <Text style={[styles.analysisCardTitle, { color: colors.accentPrimary }]}>{title}</Text>
//       <Text style={[styles.analysisCardContent, { color: colors.textPrimary }]}>{content}</Text>
//     </View>
//   );
// }

// // Main App Component
// export default function FunctionGrapher() {
//   const systemColorScheme = useColorScheme();
//   const [isDark, setIsDark] = useState(systemColorScheme === 'dark');
//   const [showLegend, setShowLegend] = useState(true);
//   const [funcInput, setFuncInput] = useState('x^2');
//   const [xMin, setXMin] = useState('-10');
//   const [xMax, setXMax] = useState('10');
//   const [yMin, setYMin] = useState('-10');
//   const [yMax, setYMax] = useState('10');
//   const [showFunction, setShowFunction] = useState(true);
//   const [showDerivative, setShowDerivative] = useState(true);
//   const [showSecondDerivative, setShowSecondDerivative] = useState(false);
//   const [showCritical, setShowCritical] = useState(true);
//   const [showRoots, setShowRoots] = useState(true);
//   const [showInflection, setShowInflection] = useState(false);
//   const [showUndefined, setShowUndefined] = useState(true);
//   const [showVerticalAsymptotes, setShowVerticalAsymptotes] = useState(true);
//   const [showHorizontalAsymptote, setShowHorizontalAsymptote] = useState(false);
//   const [showObliqueAsymptote, setShowObliqueAsymptote] = useState(false);
//   const [tangentInput, setTangentInput] = useState('');
//   const [tangentLines, setTangentLines] = useState<number[]>([]);

//   // Load theme from AsyncStorage on mount
//   useEffect(() => {
//     loadTheme();
//   }, []);

//   const loadTheme = async () => {
//     try {
//       const savedTheme = await AsyncStorage.getItem('math-grapher-theme');
//       if (savedTheme) {
//         setIsDark(savedTheme === 'dark');
//       }
//     } catch (error) {
//       console.log('Error loading theme:', error);
//     }
//   };

//   const toggleTheme = async () => {
//     const newTheme = !isDark;
//     setIsDark(newTheme);
//     try {
//       await AsyncStorage.setItem('math-grapher-theme', newTheme ? 'dark' : 'light');
//     } catch (error) {
//       console.log('Error saving theme:', error);
//     }
//   };

//   const colors = isDark ? {
//     bgPrimary: '#0a0e27',
//     bgSecondary: '#1a1f3a',
//     bgTertiary: '#252b4a',
//     textPrimary: '#e4e8f0',
//     textSecondary: '#9ca3af',
//     accentPrimary: '#6366f1',
//     accentSecondary: '#8b5cf6',
//     accentTertiary: '#ec4899',
//     borderColor: '#374151',
//     glassBg: 'rgba(26, 31, 58, 0.7)',
//     glassBorder: 'rgba(99, 102, 241, 0.2)',
//   } : {
//     bgPrimary: '#f8fafc',
//     bgSecondary: '#ffffff',
//     bgTertiary: '#f1f5f9',
//     textPrimary: '#0f172a',
//     textSecondary: '#64748b',
//     accentPrimary: '#4f46e5',
//     accentSecondary: '#7c3aed',
//     accentTertiary: '#db2777',
//     borderColor: '#e2e8f0',
//     glassBg: 'rgba(255, 255, 255, 0.7)',
//     glassBorder: 'rgba(79, 70, 229, 0.2)',
//   };

//   const analyzer = useMemo(() => {
//     try {
//       const xMinNum = parseFloat(xMin);
//       const xMaxNum = parseFloat(xMax);
//       if (isNaN(xMinNum) || isNaN(xMaxNum)) return null;
//       return new MathAnalyzer(funcInput, [xMinNum, xMaxNum]);
//     } catch {
//       return null;
//     }
//   }, [funcInput, xMin, xMax]);

//   const analysis: AnalysisResults | null = useMemo(() => {
//     if (!analyzer || analyzer.errors.length > 0) return null;
    
//     try {
//       return {
//         criticalPoints: analyzer.findCriticalPoints(),
//         roots: analyzer.findRoots(),
//         inflectionPoints: analyzer.findInflectionPoints(),
//         undefinedValues: analyzer.findUndefinedValues(),
//         verticalAsymptotes: analyzer.findVerticalAsymptotes(),
//         horizontalAsymptote: analyzer.findHorizontalAsymptote(),
//         obliqueAsymptote: analyzer.findObliqueAsymptote(),
//       };
//     } catch {
//       return null;
//     }
//   }, [analyzer]);

//   const addTangent = () => {
//     const x = parseFloat(tangentInput);
//     if (!isNaN(x) && !tangentLines.includes(x)) {
//       setTangentLines([...tangentLines, x]);
//       setTangentInput('');
//     }
//   };

//   const removeTangent = (x: number) => {
//     setTangentLines(tangentLines.filter(t => t !== x));
//   };

//   const renderGraph = () => {
//     if (!analyzer || !analysis) {
//       return (
//         <View style={[styles.graphContainer, { backgroundColor: colors.glassBg }]}>
//           <Text style={[styles.errorText, { color: colors.textPrimary }]}>
//             {analyzer?.errors.join(', ') || 'Invalid function'}
//           </Text>
//         </View>
//       );
//     }

//     const traces: any[] = [];
//     const xMinNum = parseFloat(xMin);
//     const xMaxNum = parseFloat(xMax);
//     const yMinNum = parseFloat(yMin);
//     const yMaxNum = parseFloat(yMax);

//     // Function trace
//     if (showFunction) {
//       const points = analyzer.generatePoints();
//       traces.push({
//         x: points.x,
//         y: points.y,
//         type: 'scatter',
//         mode: 'lines',
//         name: 'f(x)',
//         line: { color: '#1f77b4', width: 3 },
//       });
//     }

//     // First derivative
//     if (showDerivative) {
//       const points = analyzer.generateDerivativePoints();
//       traces.push({
//         x: points.x,
//         y: points.y,
//         type: 'scatter',
//         mode: 'lines',
//         name: "f'(x)",
//         line: { color: '#ff7f0e', width: 2, dash: 'dash' },
//       });
//     }

//     // Second derivative
//     if (showSecondDerivative) {
//       const points = analyzer.generateSecondDerivativePoints();
//       traces.push({
//         x: points.x,
//         y: points.y,
//         type: 'scatter',
//         mode: 'lines',
//         name: "f''(x)",
//         line: { color: '#2ca02c', width: 2, dash: 'dot' },
//       });
//     }

//     // Critical points
//     if (showCritical && analysis.criticalPoints.length > 0) {
//       traces.push({
//         x: analysis.criticalPoints.map(p => p.x),
//         y: analysis.criticalPoints.map(p => p.y),
//         type: 'scatter',
//         mode: 'markers',
//         name: 'Critical Points',
//         marker: { color: '#d62728', size: 12, symbol: 'circle' },
//       });
//     }

//     // Roots
//     if (showRoots && analysis.roots.length > 0) {
//       traces.push({
//         x: analysis.roots,
//         y: analysis.roots.map(() => 0),
//         type: 'scatter',
//         mode: 'markers',
//         name: 'Roots',
//         marker: { color: '#9467bd', size: 12, symbol: 'square' },
//       });
//     }

//     // Inflection points
//     if (showInflection && analysis.inflectionPoints.length > 0) {
//       traces.push({
//         x: analysis.inflectionPoints.map(p => p.x),
//         y: analysis.inflectionPoints.map(p => p.y),
//         type: 'scatter',
//         mode: 'markers',
//         name: 'Inflection Points',
//         marker: { color: '#8c564b', size: 12, symbol: 'triangle-up' },
//       });
//     }

//     // Undefined values (holes)
//     if (showUndefined && analysis.undefinedValues.length > 0) {
//       traces.push({
//         x: analysis.undefinedValues.map(p => p.x),
//         y: analysis.undefinedValues.map(p => p.y),
//         type: 'scatter',
//         mode: 'markers',
//         name: 'Undefined (Holes)',
//         marker: {
//           color: 'white',
//           size: 14,
//           symbol: 'circle',
//           line: { color: '#ff0000', width: 3 },
//         },
//       });
//     }

//     // Vertical asymptotes
//     if (showVerticalAsymptotes) {
//       analysis.verticalAsymptotes.forEach(x => {
//         traces.push({
//           x: [x, x],
//           y: [yMinNum, yMaxNum],
//           type: 'scatter',
//           mode: 'lines',
//           name: `x = ${x.toFixed(2)}`,
//           line: { color: '#e377c2', width: 2, dash: 'dashdot' },
//           showlegend: false,
//         });
//       });
//     }

//     // Horizontal asymptote
//     if (showHorizontalAsymptote && analysis.horizontalAsymptote !== null) {
//       traces.push({
//         x: [xMinNum, xMaxNum],
//         y: [analysis.horizontalAsymptote, analysis.horizontalAsymptote],
//         type: 'scatter',
//         mode: 'lines',
//         name: `y = ${analysis.horizontalAsymptote.toFixed(2)}`,
//         line: { color: '#7f7f7f', width: 2, dash: 'dashdot' },
//       });
//     }

//     // Oblique asymptote
//     if (showObliqueAsymptote && analysis.obliqueAsymptote !== null) {
//       const { m, b } = analysis.obliqueAsymptote;
//       const x_asymp = [xMinNum, xMaxNum];
//       const y_asymp = x_asymp.map(x => m * x + b);
      
//       traces.push({
//         x: x_asymp,
//         y: y_asymp,
//         type: 'scatter',
//         mode: 'lines',
//         name: `y = ${m.toFixed(2)}x + ${b.toFixed(2)}`,
//         line: { color: '#17becf', width: 2, dash: 'dashdot' },
//       });
//     }

//     // Tangent lines
//     const tangentColors = ['#2ca02c', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f'];
//     tangentLines.forEach((x0, index) => {
//       const y0 = analyzer.evaluate(x0);

//       if (!isFinite(y0)) {
//         return;
//       }

//       // Calculate left and right derivatives using limit (MATCHING HTML VERSION)
//       const slopeLeft = analyzer.evaluateDerivativeLimit(x0, 'left');
//       const slopeRight = analyzer.evaluateDerivativeLimit(x0, 'right');

//       // Check if derivatives are different (discontinuous derivative)
//       const derivativeDiffers = Math.abs(slopeLeft - slopeRight) > 1e-6;

//       if (!isFinite(slopeLeft) && !isFinite(slopeRight)) {
//         return;
//       }

//       const extend = (xMaxNum - xMinNum) * 0.15;
//       const baseColor = tangentColors[index % tangentColors.length];

//       if (derivativeDiffers && isFinite(slopeLeft) && isFinite(slopeRight)) {
//         // Draw two different tangent lines (left and right) - MATCHING HTML VERSION

//         // Left tangent
//         const x_tangent_left = [x0 - extend, x0];
//         const y_tangent_left = x_tangent_left.map(x => y0 + slopeLeft * (x - x0));

//         traces.push({
//           x: x_tangent_left,
//           y: y_tangent_left,
//           type: 'scatter',
//           mode: 'lines',
//           name: `Left tangent at x=${x0.toFixed(2)}`,
//           line: {
//             color: baseColor,
//             width: 2.5,
//             dash: 'dot',
//           },
//         });

//         // Right tangent (slightly darker color)
//         const rgb = baseColor.match(/\w\w/g)!.map(x => parseInt(x, 16) / 255);
//         const darkerColor = `rgb(${Math.max(0, rgb[0] * 255 - 40)},${Math.max(0, rgb[1] * 255 - 40)},${Math.max(0, rgb[2] * 255 - 40)})`;

//         const x_tangent_right = [x0, x0 + extend];
//         const y_tangent_right = x_tangent_right.map(x => y0 + slopeRight * (x - x0));

//         traces.push({
//           x: x_tangent_right,
//           y: y_tangent_right,
//           type: 'scatter',
//           mode: 'lines',
//           name: `Right tangent at x=${x0.toFixed(2)}`,
//           line: {
//             color: darkerColor,
//             width: 2.5,
//             dash: 'dot',
//           },
//         });
//       } else {
//         // Draw single tangent line
//         const slope = isFinite(slopeLeft) ? slopeLeft : slopeRight;

//         if (!isFinite(slope)) {
//           return;
//         }

//         const x_tangent = [x0 - extend, x0 + extend];
//         const y_tangent = x_tangent.map(x => y0 + slope * (x - x0));

//         traces.push({
//           x: x_tangent,
//           y: y_tangent,
//           type: 'scatter',
//           mode: 'lines',
//           name: `Tangent at x=${x0.toFixed(2)}`,
//           line: {
//             color: baseColor,
//             width: 2.5,
//             dash: 'dot',
//           },
//         });
//       }

//       // Add point at tangent location
//       traces.push({
//         x: [x0],
//         y: [y0],
//         type: 'scatter',
//         mode: 'markers',
//         name: `Point at x=${x0.toFixed(2)}`,
//         marker: {
//           color: baseColor,
//           size: 10,
//           line: { color: 'black', width: 2 },
//         },
//         showlegend: false,
//       });
//     });

//     const isSmallScreen = SCREEN_WIDTH <= 768;

//     const layout = {
//       title: {
//         text: `f(x) = ${funcInput}`,
//         font: {
//           family: 'Courier',
//           size: 18,
//           color: isDark ? '#e4e8f0' : '#0f172a',
//         },
//       },
//       xaxis: {
//         title: 'x',
//         range: [xMinNum, xMaxNum],
//         gridcolor: isDark ? '#374151' : '#e2e8f0',
//         zerolinecolor: isDark ? '#6366f1' : '#4f46e5',
//         color: isDark ? '#e4e8f0' : '#0f172a',
//       },
//       yaxis: {
//         title: 'y',
//         range: [yMinNum, yMaxNum],
//         gridcolor: isDark ? '#374151' : '#e2e8f0',
//         zerolinecolor: isDark ? '#6366f1' : '#4f46e5',
//         color: isDark ? '#e4e8f0' : '#0f172a',
//       },
//       plot_bgcolor: isDark ? '#1a1f3a' : '#ffffff',
//       paper_bgcolor: isDark ? '#1a1f3a' : '#ffffff',
//       font: { color: isDark ? '#e4e8f0' : '#0f172a' },
//       showlegend: showLegend,
//       legend: {
//         bgcolor: isDark ? 'rgba(26, 31, 58, 0.8)' : 'rgba(255, 255, 255, 0.8)',
//         bordercolor: isDark ? '#6366f1' : '#4f46e5',
//         borderwidth: 1,
//         orientation: isSmallScreen ? 'h' : 'v',
//         x: isSmallScreen ? 0.5 : 1.02,
//         y: isSmallScreen ? 1.25 : 1,
//         xanchor: isSmallScreen ? 'center' : 'left',
//         yanchor: isSmallScreen ? 'top' : 'top',
//       },
//       margin: {
//         t: isSmallScreen ? 150 : 80,
//         b: 60,
//         l: 60,
//         r: isSmallScreen ? 20 : 200,
//       },
//     };

//     const config = {
//       displayModeBar: true,
//       displaylogo: false,
//       responsive: true,
//     };

//     return (
//       <View style={[styles.graphContainer, { backgroundColor: colors.glassBg, borderColor: colors.glassBorder }]}>
//         <Plotly
//           data={traces}
//           layout={layout}
//           config={config}
//           style={styles.plotlyGraph}
//         />
//       </View>
//     );
//   };

//   return (
//     <View style={[styles.container, { backgroundColor: colors.bgPrimary }]}>
//       <StatusBar barStyle={isDark ? 'light-content' : 'dark-content'} />
      
//       {/* Header with theme and legend toggles */}
//       <View style={styles.header}>
//         <View style={styles.headerContent}>
//           <Text style={[styles.title, { color: colors.accentPrimary }]}>∫ Function Grapher</Text>
//           <Text style={[styles.subtitle, { color: colors.textSecondary }]}>
//             Real-time mathematical visualization & analysis
//           </Text>
//         </View>
//         <View style={styles.headerButtons}>
//           <TouchableOpacity
//             style={[styles.headerButton, { backgroundColor: colors.glassBg, borderColor: colors.glassBorder }]}
//             onPress={() => setShowLegend(!showLegend)}
//           >
//             <Text style={{ fontSize: 16 }}>📊</Text>
//           </TouchableOpacity>
//           <TouchableOpacity
//             style={[styles.headerButton, { backgroundColor: colors.glassBg, borderColor: colors.glassBorder }]}
//             onPress={toggleTheme}
//           >
//             <Text style={{ fontSize: 16 }}>{isDark ? '🌙' : '☀️'}</Text>
//           </TouchableOpacity>
//         </View>
//       </View>

//       <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
//         {/* Input Section */}
//         <View style={[styles.section, { backgroundColor: colors.glassBg, borderColor: colors.glassBorder }]}>
//           <Text style={[styles.label, { color: colors.textSecondary }]}>FUNCTION f(x)</Text>
//           <TextInput
//             style={[styles.input, { backgroundColor: colors.bgSecondary, borderColor: colors.borderColor, color: colors.textPrimary }]}
//             value={funcInput}
//             onChangeText={setFuncInput}
//             placeholder="e.g., x^2, sin(x), (x²-1)/(x-1)"
//             placeholderTextColor={colors.textSecondary}
//           />

//           <View style={styles.rangeGrid}>
//             <View style={styles.rangeItem}>
//               <Text style={[styles.label, { color: colors.textSecondary }]}>X MIN</Text>
//               <TextInput
//                 style={[styles.inputSmall, { backgroundColor: colors.bgSecondary, borderColor: colors.borderColor, color: colors.textPrimary }]}
//                 value={xMin}
//                 onChangeText={setXMin}
//                 keyboardType="numeric"
//                 placeholderTextColor={colors.textSecondary}
//               />
//             </View>
//             <View style={styles.rangeItem}>
//               <Text style={[styles.label, { color: colors.textSecondary }]}>X MAX</Text>
//               <TextInput
//                 style={[styles.inputSmall, { backgroundColor: colors.bgSecondary, borderColor: colors.borderColor, color: colors.textPrimary }]}
//                 value={xMax}
//                 onChangeText={setXMax}
//                 keyboardType="numeric"
//                 placeholderTextColor={colors.textSecondary}
//               />
//             </View>
//             <View style={styles.rangeItem}>
//               <Text style={[styles.label, { color: colors.textSecondary }]}>Y MIN</Text>
//               <TextInput
//                 style={[styles.inputSmall, { backgroundColor: colors.bgSecondary, borderColor: colors.borderColor, color: colors.textPrimary }]}
//                 value={yMin}
//                 onChangeText={setYMin}
//                 keyboardType="numeric"
//                 placeholderTextColor={colors.textSecondary}
//               />
//             </View>
//             <View style={styles.rangeItem}>
//               <Text style={[styles.label, { color: colors.textSecondary }]}>Y MAX</Text>
//               <TextInput
//                 style={[styles.inputSmall, { backgroundColor: colors.bgSecondary, borderColor: colors.borderColor, color: colors.textPrimary }]}
//                 value={yMax}
//                 onChangeText={setYMax}
//                 keyboardType="numeric"
//                 placeholderTextColor={colors.textSecondary}
//               />
//             </View>
//           </View>

//           {/* Display Options */}
//           <View style={styles.controlsGrid}>
//             <CheckboxItem label="Function f(x)" checked={showFunction} onToggle={setShowFunction} colors={colors} color="#1f77b4" />
//             <CheckboxItem label="Derivative f'(x)" checked={showDerivative} onToggle={setShowDerivative} colors={colors} color="#ff7f0e" />
//             <CheckboxItem label="2nd Derivative" checked={showSecondDerivative} onToggle={setShowSecondDerivative} colors={colors} color="#2ca02c" />
//             <CheckboxItem label="Critical Points" checked={showCritical} onToggle={setShowCritical} colors={colors} color="#d62728" />
//             <CheckboxItem label="Roots" checked={showRoots} onToggle={setShowRoots} colors={colors} color="#9467bd" />
//             <CheckboxItem label="Inflection" checked={showInflection} onToggle={setShowInflection} colors={colors} color="#8c564b" />
//             <CheckboxItem label="Undefined" checked={showUndefined} onToggle={setShowUndefined} colors={colors} color="#ff0000" />
//             <CheckboxItem label="Vert. Asymptotes" checked={showVerticalAsymptotes} onToggle={setShowVerticalAsymptotes} colors={colors} color="#e377c2" />
//             <CheckboxItem label="Horiz. Asymptote" checked={showHorizontalAsymptote} onToggle={setShowHorizontalAsymptote} colors={colors} color="#7f7f7f" />
//             <CheckboxItem label="Oblique Asymptote" checked={showObliqueAsymptote} onToggle={setShowObliqueAsymptote} colors={colors} color="#17becf" />
//           </View>

//           {/* Tangent Lines */}
//           <View style={styles.tangentSection}>
//             <Text style={[styles.label, { color: colors.textSecondary }]}>ADD TANGENT LINE</Text>
//             <View style={styles.tangentControls}>
//               <TextInput
//                 style={[styles.inputSmall, { flex: 1, backgroundColor: colors.bgSecondary, borderColor: colors.borderColor, color: colors.textPrimary }]}
//                 value={tangentInput}
//                 onChangeText={setTangentInput}
//                 placeholder="x-coordinate"
//                 keyboardType="numeric"
//                 placeholderTextColor={colors.textSecondary}
//               />
//               <TouchableOpacity
//                 style={[styles.button, { backgroundColor: colors.accentPrimary }]}
//                 onPress={addTangent}
//               >
//                 <Text style={styles.buttonText}>Add</Text>
//               </TouchableOpacity>
//             </View>
//             <View style={styles.tangentList}>
//               {tangentLines.map((x, idx) => (
//                 <View key={idx} style={[styles.tangentTag, { backgroundColor: colors.bgTertiary, borderColor: colors.borderColor }]}>
//                   <Text style={[styles.tangentTagText, { color: colors.textPrimary }]}>
//                     x = {x.toFixed(2)}
//                   </Text>
//                   <TouchableOpacity onPress={() => removeTangent(x)}>
//                     <Text style={styles.removeButton}>×</Text>
//                   </TouchableOpacity>
//                 </View>
//               ))}
//             </View>
//           </View>
//         </View>

//         {/* Graph */}
//         {renderGraph()}

//         {/* Analysis */}
//         {analysis && (
//           <View style={[styles.section, { backgroundColor: colors.glassBg, borderColor: colors.glassBorder }]}>
//             <Text style={[styles.sectionTitle, { color: colors.textPrimary }]}>Mathematical Analysis</Text>
            
//             <AnalysisCard
//               title="Function Expressions"
//               content={`f(x) = ${funcInput}\nf'(x) = ${analyzer?.derivNode.toString()}\nf''(x) = ${analyzer?.secondDerivNode.toString()}`}
//               colors={colors}
//             />

//             <AnalysisCard
//               title={`Critical Points (${analysis.criticalPoints.length})`}
//               content={analysis.criticalPoints.length > 0
//                 ? analysis.criticalPoints.map(p => `(${p.x.toFixed(4)}, ${p.y.toFixed(4)})`).join('\n')
//                 : 'None found'}
//               colors={colors}
//             />

//             <AnalysisCard
//               title={`Roots/Zeros (${analysis.roots.length})`}
//               content={analysis.roots.length > 0
//                 ? analysis.roots.map(r => `x = ${r.toFixed(4)}`).join('\n')
//                 : 'None found'}
//               colors={colors}
//             />

//             <AnalysisCard
//               title={`Inflection Points (${analysis.inflectionPoints.length})`}
//               content={analysis.inflectionPoints.length > 0
//                 ? analysis.inflectionPoints.map(p => `(${p.x.toFixed(4)}, ${p.y.toFixed(4)})`).join('\n')
//                 : 'None found'}
//               colors={colors}
//             />

//             <AnalysisCard
//               title={`Undefined Values (Holes) (${analysis.undefinedValues.length})`}
//               content={analysis.undefinedValues.length > 0
//                 ? analysis.undefinedValues.map(p => `x = ${p.x.toFixed(4)}, limit = ${p.y.toFixed(4)}`).join('\n')
//                 : 'None found'}
//               colors={colors}
//             />

//             <AnalysisCard
//               title="Asymptotes"
//               content={[
//                 analysis.verticalAsymptotes.length > 0 ? `Vertical:\n${analysis.verticalAsymptotes.map(a => `x = ${a.toFixed(4)}`).join('\n')}` : '',
//                 analysis.horizontalAsymptote !== null ? `Horizontal:\ny = ${analysis.horizontalAsymptote.toFixed(4)}` : '',
//                 analysis.obliqueAsymptote !== null ? `Oblique:\ny = ${analysis.obliqueAsymptote.m.toFixed(4)}x + ${analysis.obliqueAsymptote.b.toFixed(4)}` : ''
//               ].filter(Boolean).join('\n\n') || 'None found'}
//               colors={colors}
//             />

//             <AnalysisCard
//               title="Domain"
//               content={`All real numbers ℝ\n(computed over [${xMin}, ${xMax}])`}
//               colors={colors}
//             />
//           </View>
//         )}
//       </ScrollView>
//     </View>
//   );
// }

// const styles = StyleSheet.create({
//   container: {
//     flex: 1,
//     paddingTop: Platform.OS === 'ios' ? 50 : StatusBar.currentHeight || 0,
//   },
//   scrollView: {
//     flex: 1,
//   },
//   header: {
//     flexDirection: 'row',
//     justifyContent: 'space-between',
//     alignItems: 'center',
//     paddingHorizontal: 20,
//     paddingVertical: 20,
//   },
//   headerContent: {
//     flex: 1,
//   },
//   headerButtons: {
//     flexDirection: 'row',
//     gap: 10,
//   },
//   headerButton: {
//     width: 44,
//     height: 44,
//     borderRadius: 22,
//     borderWidth: 1,
//     justifyContent: 'center',
//     alignItems: 'center',
//   },
//   title: {
//     fontSize: 28,
//     fontWeight: '700',
//     marginBottom: 4,
//     fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
//   },
//   subtitle: {
//     fontSize: 12,
//     fontWeight: '400',
//     fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
//   },
//   section: {
//     marginHorizontal: 20,
//     marginBottom: 20,
//     padding: 20,
//     borderRadius: 20,
//     borderWidth: 1,
//   },
//   label: {
//     fontSize: 12,
//     fontWeight: '600',
//     marginBottom: 8,
//     textTransform: 'uppercase',
//     letterSpacing: 0.5,
//     fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
//   },
//   input: {
//     width: '100%',
//     padding: 16,
//     borderRadius: 12,
//     borderWidth: 2,
//     fontSize: 16,
//     fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
//     marginBottom: 16,
//   },
//   inputSmall: {
//     padding: 12,
//     borderRadius: 12,
//     borderWidth: 2,
//     fontSize: 14,
//     fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
//   },
//   rangeGrid: {
//     flexDirection: 'row',
//     flexWrap: 'wrap',
//     gap: 12,
//     marginBottom: 16,
//   },
//   rangeItem: {
//     flex: 1,
//     minWidth: 150,
//   },
//   controlsGrid: {
//     marginTop: 16,
//     gap: 8,
//   },
//   controlItem: {
//     flexDirection: 'row',
//     alignItems: 'center',
//     padding: 12,
//     borderRadius: 12,
//     borderWidth: 2,
//     gap: 12,
//   },
//   checkbox: {
//     width: 20,
//     height: 20,
//     borderRadius: 6,
//     borderWidth: 2,
//     justifyContent: 'center',
//     alignItems: 'center',
//   },
//   checkmark: {
//     color: 'white',
//     fontSize: 14,
//     fontWeight: 'bold',
//   },
//   controlLabel: {
//     flex: 1,
//     fontSize: 14,
//     fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
//   },
//   colorIndicator: {
//     width: 12,
//     height: 12,
//     borderRadius: 6,
//   },
//   tangentSection: {
//     marginTop: 16,
//     paddingTop: 16,
//     borderTopWidth: 1,
//   },
//   tangentControls: {
//     flexDirection: 'row',
//     gap: 12,
//     marginBottom: 12,
//   },
//   button: {
//     paddingHorizontal: 24,
//     paddingVertical: 12,
//     borderRadius: 12,
//     justifyContent: 'center',
//     alignItems: 'center',
//   },
//   buttonText: {
//     color: 'white',
//     fontSize: 14,
//     fontWeight: '600',
//     textTransform: 'uppercase',
//     fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
//   },
//   tangentList: {
//     flexDirection: 'row',
//     flexWrap: 'wrap',
//     gap: 8,
//   },
//   tangentTag: {
//     flexDirection: 'row',
//     alignItems: 'center',
//     padding: 8,
//     borderRadius: 20,
//     borderWidth: 1,
//     gap: 8,
//   },
//   tangentTagText: {
//     fontSize: 12,
//     fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
//   },
//   removeButton: {
//     fontSize: 20,
//     color: '#ef4444',
//   },
//   graphContainer: {
//     marginHorizontal: 20,
//     marginBottom: 20,
//     padding: 20,
//     borderRadius: 20,
//     borderWidth: 1,
//     position: 'relative',
//     height: GRAPH_HEIGHT + 80, // Account for padding
//   },
//   plotlyGraph: {
//     flex: 1,
//     width: '100%',
//   },
//   errorText: {
//     fontSize: 14,
//     fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
//     textAlign: 'center',
//     padding: 20,
//   },
//   sectionTitle: {
//     fontSize: 20,
//     fontWeight: '600',
//     marginBottom: 16,
//     fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
//   },
//   analysisCard: {
//     backgroundColor: '#1a1f3a',
//     borderRadius: 12,
//     padding: 16,
//     marginBottom: 12,
//     borderLeftWidth: 4,
//   },
//   analysisCardTitle: {
//     fontSize: 14,
//     fontWeight: '600',
//     marginBottom: 8,
//     textTransform: 'uppercase',
//     fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
//   },
//   analysisCardContent: {
//     fontSize: 13,
//     lineHeight: 20,
//     fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
//   },
// });

// import React, { useState, useEffect, useMemo, useRef } from 'react';
// import {
//   View,
//   Text,
//   TextInput,
//   ScrollView,
//   TouchableOpacity,
//   StyleSheet,
//   Dimensions,
//   useColorScheme,
//   Platform,
//   StatusBar,
//   Alert,
// } from 'react-native';
// import AsyncStorage from '@react-native-async-storage/async-storage';
// import Plotly from 'react-native-plotly';
// import * as math from 'mathjs';
// import { captureRef } from 'react-native-view-shot';
// import * as Sharing from 'expo-sharing';
// import * as FileSystem from 'expo-file-system';

// const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');
// const GRAPH_WIDTH = SCREEN_WIDTH - 40;
// const GRAPH_HEIGHT = 300;

// // Types
// interface Point {
//   x: number;
//   y: number;
// }

// interface AsymptoteOblique {
//   m: number;
//   b: number;
// }

// interface AnalysisResults {
//   criticalPoints: Point[];
//   roots: number[];
//   inflectionPoints: Point[];
//   undefinedValues: Point[];
//   verticalAsymptotes: number[];
//   horizontalAsymptote: number | null;
//   obliqueAsymptote: AsymptoteOblique | null;
// }

// // Math Analyzer Class - Keep this EXACTLY the same as HTML version
// class MathAnalyzer {
//   funcStr: string;
//   xRange: [number, number];
//   numPoints: number;
//   node: any;
//   func: any;
//   derivNode: any;
//   deriv: any;
//   secondDerivNode: any;
//   secondDeriv: any;
//   errors: string[];

//   constructor(funcStr: string, xRange: [number, number], numPoints = 1000) {
//     this.funcStr = this.normalizeFunction(funcStr);
//     this.xRange = xRange;
//     this.numPoints = numPoints;
//     this.errors = [];

//     try {
//       this.node = math.parse(this.funcStr);
//       this.func = this.node.compile();

//       // Keep original for undefined detection
//       this.funcOriginal = this.func;

//       this.derivNode = math.derivative(this.node, 'x');
//       this.deriv = this.derivNode.compile();
//       this.secondDerivNode = math.derivative(this.derivNode, 'x');
//       this.secondDeriv = this.secondDerivNode.compile();
//     } catch (e: any) {
//       this.errors.push(`Parse error: ${e.message}`);
//     }
//   }

//   normalizeFunction(input: string): string {
//     let normalized = input;
//     normalized = normalized.replace(/²/g, '^2');
//     normalized = normalized.replace(/³/g, '^3');
//     normalized = normalized.replace(/⁴/g, '^4');
//     normalized = normalized.replace(/⁵/g, '^5');
//     normalized = normalized.replace(/⁶/g, '^6');
//     normalized = normalized.replace(/\*\*/g, '^');

//     const openParen = (normalized.match(/\(/g) || []).length;
//     const closeParen = (normalized.match(/\)/g) || []).length;
//     if (openParen > closeParen) {
//       normalized += ')'.repeat(openParen - closeParen);
//     }

//     const openSquare = (normalized.match(/\[/g) || []).length;
//     const closeSquare = (normalized.match(/\]/g) || []).length;
//     if (openSquare > closeSquare) {
//       normalized += ']'.repeat(openSquare - closeSquare);
//     }

//     normalized = normalized.replace(/sqrt/gi, 'sqrt');
//     normalized = normalized.replace(/abs/gi, 'abs');

//     return normalized;
//   }

//   evaluate(x: number): number {
//     try {
//       const result = this.func.evaluate({ x });
//       return isFinite(result) ? result : NaN;
//     } catch {
//       return NaN;
//     }
//   }

//   evaluateDerivative(x: number): number {
//     try {
//       const result = this.deriv.evaluate({ x });
//       return isFinite(result) ? result : NaN;
//     } catch {
//       return NaN;
//     }
//   }

//   evaluateSecondDerivative(x: number): number {
//     try {
//       const result = this.secondDeriv.evaluate({ x });
//       return isFinite(result) ? result : NaN;
//     } catch {
//       return NaN;
//     }
//   }

//   evaluateDerivativeLimit(x: number, direction: 'left' | 'right' | 'both' = 'both'): number {
//     const h = 1e-7;
//     if (direction === 'left') {
//       const f_x = this.evaluate(x);
//       const f_x_h = this.evaluate(x - h);
//       return (f_x - f_x_h) / h;
//     } else if (direction === 'right') {
//       const f_x = this.evaluate(x);
//       const f_x_h = this.evaluate(x + h);
//       return (f_x_h - f_x) / h;
//     } else {
//       const f_x_h = this.evaluate(x + h);
//       const f_x_h_neg = this.evaluate(x - h);
//       return (f_x_h - f_x_h_neg) / (2 * h);
//     }
//   }

//   generatePoints(): { x: number[], y: number[] } {
//     const [xMin, xMax] = this.xRange;
//     const step = (xMax - xMin) / this.numPoints;
//     const x: number[] = [];
//     const y: number[] = [];

//     for (let i = 0; i <= this.numPoints; i++) {
//       const xVal = xMin + i * step;
//       const yVal = this.evaluate(xVal);
//       x.push(xVal);
//       y.push(yVal);
//     }

//     return { x, y };
//   }

//   generateDerivativePoints(): { x: number[], y: number[] } {
//     const [xMin, xMax] = this.xRange;
//     const step = (xMax - xMin) / this.numPoints;
//     const x: number[] = [];
//     const y: number[] = [];

//     for (let i = 0; i <= this.numPoints; i++) {
//       const xVal = xMin + i * step;
//       const yVal = this.evaluateDerivative(xVal);
//       x.push(xVal);
//       y.push(yVal);
//     }

//     return { x, y };
//   }

//   generateSecondDerivativePoints(): { x: number[], y: number[] } {
//     const [xMin, xMax] = this.xRange;
//     const step = (xMax - xMin) / this.numPoints;
//     const x: number[] = [];
//     const y: number[] = [];

//     for (let i = 0; i <= this.numPoints; i++) {
//       const xVal = xMin + i * step;
//       const yVal = this.evaluateSecondDerivative(xVal);
//       x.push(xVal);
//       y.push(yVal);
//     }

//     return { x, y };
//   }

//   bisectionMethod(a: number, b: number, tolerance = 0.0001, maxIter = 50): number | null {
//     let fa = this.evaluate(a);
//     let fb = this.evaluate(b);

//     if (fa * fb > 0) return null;

//     for (let i = 0; i < maxIter; i++) {
//       const c = (a + b) / 2;
//       const fc = this.evaluate(c);

//       if (Math.abs(fc) < tolerance || (b - a) / 2 < tolerance) {
//         return c;
//       }

//       if (fa * fc < 0) {
//         b = c;
//         fb = fc;
//       } else {
//         a = c;
//         fa = fc;
//       }
//     }

//     return (a + b) / 2;
//   }

//   findRoots(): number[] {
//     const [xMin, xMax] = this.xRange;
//     const step = (xMax - xMin) / 1000;
//     const roots: number[] = [];
//     let prevY = this.evaluate(xMin);

//     for (let x = xMin + step; x <= xMax; x += step) {
//       const y = this.evaluate(x);
//       if (!isNaN(y) && !isNaN(prevY)) {
//         if (prevY * y < 0 || Math.abs(y) < 0.001) {
//           const root = this.bisectionMethod(x - step, x);
//           if (root !== null && !roots.some((r) => Math.abs(r - root) < 0.01)) {
//             roots.push(root);
//           }
//         }
//       }
//       prevY = y;
//     }

//     return roots;
//   }

//   bisectionDerivative(a: number, b: number, tolerance = 0.0001, maxIter = 50): number | null {
//     let fa = this.evaluateDerivative(a);
//     let fb = this.evaluateDerivative(b);

//     if (fa * fb > 0) return null;

//     for (let i = 0; i < maxIter; i++) {
//       const c = (a + b) / 2;
//       const fc = this.evaluateDerivative(c);

//       if (Math.abs(fc) < tolerance || (b - a) / 2 < tolerance) {
//         return c;
//       }

//       if (fa * fc < 0) {
//         b = c;
//         fb = fc;
//       } else {
//         a = c;
//         fa = fc;
//       }
//     }

//     return (a + b) / 2;
//   }

//   findCriticalPoints(): Point[] {
//     const [xMin, xMax] = this.xRange;
//     const step = (xMax - xMin) / 1000;
//     const criticalPoints: Point[] = [];
//     let prevDy = this.evaluateDerivative(xMin);

//     for (let x = xMin + step; x <= xMax; x += step) {
//       const dy = this.evaluateDerivative(x);
//       if (!isNaN(dy) && !isNaN(prevDy)) {
//         if (prevDy * dy < 0 || Math.abs(dy) < 0.001) {
//           const critX = this.bisectionDerivative(x - step, x);
//           if (critX !== null && !criticalPoints.some((p) => Math.abs(p.x - critX) < 0.01)) {
//             const critY = this.evaluate(critX);
//             if (!isNaN(critY)) {
//               criticalPoints.push({ x: critX, y: critY });
//             }
//           }
//         }
//       }
//       prevDy = dy;
//     }

//     return criticalPoints;
//   }

//   bisectionSecondDerivative(a: number, b: number, tolerance = 0.0001, maxIter = 50): number | null {
//     let fa = this.evaluateSecondDerivative(a);
//     let fb = this.evaluateSecondDerivative(b);

//     if (fa * fb > 0) return null;

//     for (let i = 0; i < maxIter; i++) {
//       const c = (a + b) / 2;
//       const fc = this.evaluateSecondDerivative(c);

//       if (Math.abs(fc) < tolerance || (b - a) / 2 < tolerance) {
//         return c;
//       }

//       if (fa * fc < 0) {
//         b = c;
//         fb = fc;
//       } else {
//         a = c;
//         fa = fc;
//       }
//     }

//     return (a + b) / 2;
//   }

//   findInflectionPoints(): Point[] {
//     const [xMin, xMax] = this.xRange;
//     const step = (xMax - xMin) / 1000;
//     const inflectionPoints: Point[] = [];
//     let prevDdy = this.evaluateSecondDerivative(xMin);

//     for (let x = xMin + step; x <= xMax; x += step) {
//       const ddy = this.evaluateSecondDerivative(x);
//       if (!isNaN(ddy) && !isNaN(prevDdy)) {
//         if (prevDdy * ddy < 0 || Math.abs(ddy) < 0.001) {
//           const inflX = this.bisectionSecondDerivative(x - step, x);
//           if (inflX !== null && !inflectionPoints.some((p) => Math.abs(p.x - inflX) < 0.01)) {
//             const inflY = this.evaluate(inflX);
//             if (!isNaN(inflY)) {
//               inflectionPoints.push({ x: inflX, y: inflY });
//             }
//           }
//         }
//       }
//       prevDdy = ddy;
//     }

//     return inflectionPoints;
//   }

//   findUndefinedValues(): Point[] {
//     const [xMin, xMax] = this.xRange;
//     const undefined: Point[] = [];

//     if (!this.funcStr.includes('/')) {
//       return [];
//     }

//     const step = (xMax - xMin) / 1000;

//     for (let x = xMin; x <= xMax; x += step) {
//       const y = this.evaluate(x);

//       if (isNaN(y) || !isFinite(y)) {
//         const h = 0.0001;
//         const leftVal = this.evaluate(x - h);
//         const rightVal = this.evaluate(x + h);

//         if (isFinite(leftVal) && isFinite(rightVal) && Math.abs(leftVal - rightVal) < 0.01) {
//           const limitVal = (leftVal + rightVal) / 2;

//           if (!undefined.some((p) => Math.abs(p.x - x) < step * 2)) {
//             undefined.push({ x, y: limitVal });
//           }
//         }
//       }
//     }

//     return undefined;
//   }

//   findVerticalAsymptotes(): number[] {
//     const [xMin, xMax] = this.xRange;
//     const step = (xMax - xMin) / 1000;
//     const asymptotes: number[] = [];
//     let prevY = this.evaluate(xMin);

//     for (let x = xMin + step; x <= xMax; x += step) {
//       const y = this.evaluate(x);

//       if ((isFinite(prevY) && !isFinite(y)) || (!isFinite(prevY) && isFinite(y))) {
//         const h = 0.0001;
//         const leftVal = this.evaluate(x - h);
//         const rightVal = this.evaluate(x + h);

//         if (!isFinite(leftVal) || !isFinite(rightVal) || Math.abs(leftVal - rightVal) > 10) {
//           if (!asymptotes.some((a) => Math.abs(a - x) < step * 2)) {
//             asymptotes.push(x);
//           }
//         }
//       } else if (isFinite(prevY) && isFinite(y) && Math.abs(y - prevY) > 1000) {
//         if (!asymptotes.some((a) => Math.abs(a - x) < step * 2)) {
//           asymptotes.push(x);
//         }
//       }

//       prevY = y;
//     }

//     return asymptotes;
//   }

//   findHorizontalAsymptote(): number | null {
//     const farRight = this.evaluate(this.xRange[1] * 10);
//     const farLeft = this.evaluate(this.xRange[0] * 10);

//     if (isFinite(farRight) && isFinite(farLeft) && Math.abs(farRight - farLeft) < 0.1) {
//       return (farRight + farLeft) / 2;
//     }

//     return null;
//   }

//   findObliqueAsymptote(): AsymptoteOblique | null {
//     if (this.findHorizontalAsymptote() !== null) {
//       return null;
//     }

//     const [xMin, xMax] = this.xRange;
//     const xLarge = Math.max(Math.abs(xMin), Math.abs(xMax)) * 10;

//     const f_pos = this.evaluate(xLarge);
//     const f_neg = this.evaluate(-xLarge);

//     if (!isFinite(f_pos) || !isFinite(f_neg)) {
//       return null;
//     }

//     const m_pos = f_pos / xLarge;
//     const m_neg = f_neg / -xLarge;

//     if (!isFinite(m_pos) || !isFinite(m_neg) || Math.abs(m_pos) < 0.001 || Math.abs(m_neg) < 0.001) {
//       return null;
//     }

//     if (Math.abs(m_pos - m_neg) > 0.1) {
//       return null;
//     }

//     const m = (m_pos + m_neg) / 2;
//     const b_pos = f_pos - m * xLarge;
//     const b_neg = f_neg - m * -xLarge;

//     if (!isFinite(b_pos) || !isFinite(b_neg)) {
//       return null;
//     }

//     if (Math.abs(b_pos - b_neg) > 1) {
//       return null;
//     }

//     const b = (b_pos + b_neg) / 2;

//     return { m, b };
//   }
// }

// // Checkbox Component
// function CheckboxItem({ 
//   label, 
//   checked, 
//   onToggle, 
//   colors, 
//   color 
// }: { 
//   label: string; 
//   checked: boolean; 
//   onToggle: (val: boolean) => void; 
//   colors: any; 
//   color: string;
// }) {
//   return (
//     <TouchableOpacity
//       style={[styles.controlItem, { backgroundColor: colors.bgSecondary, borderColor: colors.borderColor }]}
//       onPress={() => onToggle(!checked)}
//     >
//       <View style={[styles.checkbox, { borderColor: colors.borderColor, backgroundColor: checked ? colors.accentPrimary : 'transparent' }]}>
//         {checked && <Text style={styles.checkmark}>✓</Text>}
//       </View>
//       <Text style={[styles.controlLabel, { color: colors.textPrimary }]}>{label}</Text>
//       <View style={[styles.colorIndicator, { backgroundColor: color }]} />
//     </TouchableOpacity>
//   );
// }

// // Analysis Card Component
// function AnalysisCard({ 
//   title, 
//   content, 
//   colors 
// }: { 
//   title: string; 
//   content: string; 
//   colors: any;
// }) {
//   return (
//     <View style={[styles.analysisCard, { backgroundColor: colors.bgSecondary, borderLeftColor: colors.accentPrimary }]}>
//       <Text style={[styles.analysisCardTitle, { color: colors.accentPrimary }]}>{title}</Text>
//       <Text style={[styles.analysisCardContent, { color: colors.textPrimary }]}>{content}</Text>
//     </View>
//   );
// }

// // Main App Component
// export default function FunctionGrapher() {
//   const systemColorScheme = useColorScheme();
//   const [isDark, setIsDark] = useState(systemColorScheme === 'dark');
//   const [showLegend, setShowLegend] = useState(true);
//   const [funcInput, setFuncInput] = useState('x^2');
//   const [xMin, setXMin] = useState('-10');
//   const [xMax, setXMax] = useState('10');
//   const [yMin, setYMin] = useState('-10');
//   const [yMax, setYMax] = useState('10');
//   const [showFunction, setShowFunction] = useState(true);
//   const [showDerivative, setShowDerivative] = useState(true);
//   const [showSecondDerivative, setShowSecondDerivative] = useState(false);
//   const [showCritical, setShowCritical] = useState(true);
//   const [showRoots, setShowRoots] = useState(true);
//   const [showInflection, setShowInflection] = useState(false);
//   const [showUndefined, setShowUndefined] = useState(true);
//   const [showVerticalAsymptotes, setShowVerticalAsymptotes] = useState(true);
//   const [showHorizontalAsymptote, setShowHorizontalAsymptote] = useState(false);
//   const [showObliqueAsymptote, setShowObliqueAsymptote] = useState(false);
//   const [tangentInput, setTangentInput] = useState('');
//   const [tangentLines, setTangentLines] = useState<number[]>([]);
//   const graphRef = useRef<View>(null);

//   // Load theme from AsyncStorage on mount
//   useEffect(() => {
//     loadTheme();
//   }, []);

//   const loadTheme = async () => {
//     try {
//       const savedTheme = await AsyncStorage.getItem('math-grapher-theme');
//       if (savedTheme) {
//         setIsDark(savedTheme === 'dark');
//       }
//     } catch (error) {
//       console.log('Error loading theme:', error);
//     }
//   };

//   const toggleTheme = async () => {
//     const newTheme = !isDark;
//     setIsDark(newTheme);
//     try {
//       await AsyncStorage.setItem('math-grapher-theme', newTheme ? 'dark' : 'light');
//     } catch (error) {
//       console.log('Error saving theme:', error);
//     }
//   };

//   const handleDownloadPlot = async () => {
//     try {
//       if (!graphRef.current) {
//         Alert.alert('Error', 'Graph not ready');
//         return;
//       }

//       // Capture the graph view as image
//       const uri = await captureRef(graphRef, {
//         format: 'png',
//         quality: 1,
//         result: 'tmpfile',
//       });

//       // Copy to a permanent location with proper filename
//       const timestamp = new Date().getTime();
//       const filename = `plot_${timestamp}.png`;
//       const destUri = `${cacheDirectory}${filename}`;
      
//       await FileSystem.copyAsync({
//         from: uri,
//         to: destUri
//       });

//       // Use sharing dialog to save
//       const sharingAvailable = await Sharing.isAvailableAsync();
//       if (sharingAvailable) {
//         await Sharing.shareAsync(destUri, {
//           mimeType: 'image/png',
//           dialogTitle: 'Save Plot to Gallery',
//           UTI: 'public.png'
//         });
//       } else {
//         Alert.alert('Success', `Plot saved to: ${destUri}`);
//       }
//     } catch (error) {
//       console.error('Error saving plot:', error);
//       Alert.alert('Error', 'Failed to save plot');
//     }
//   };

//   const handleSharePlot = async () => {
//     try {
//       if (!graphRef.current) {
//         Alert.alert('Error', 'Graph not ready');
//         return;
//       }

//       // Capture the graph view as image
//       const uri = await captureRef(graphRef, {
//         format: 'png',
//         quality: 1,
//         result: 'tmpfile',
//       });

//       // Share directly
//       const sharingAvailable = await Sharing.isAvailableAsync();
//       if (sharingAvailable) {
//         await Sharing.shareAsync(uri, {
//           mimeType: 'image/png',
//           dialogTitle: 'Share Plot',
//         });
//       } else {
//         Alert.alert('Info', 'Sharing not available');
//       }
//     } catch (error) {
//       console.error('Error sharing plot:', error);
//       Alert.alert('Error', 'Failed to share plot');
//     }
//   };

//   const colors = isDark ? {
//     bgPrimary: '#0a0e27',
//     bgSecondary: '#1a1f3a',
//     bgTertiary: '#252b4a',
//     textPrimary: '#e4e8f0',
//     textSecondary: '#9ca3af',
//     accentPrimary: '#6366f1',
//     accentSecondary: '#8b5cf6',
//     accentTertiary: '#ec4899',
//     borderColor: '#374151',
//     glassBg: 'rgba(26, 31, 58, 0.7)',
//     glassBorder: 'rgba(99, 102, 241, 0.2)',
//   } : {
//     bgPrimary: '#f8fafc',
//     bgSecondary: '#ffffff',
//     bgTertiary: '#f1f5f9',
//     textPrimary: '#0f172a',
//     textSecondary: '#64748b',
//     accentPrimary: '#4f46e5',
//     accentSecondary: '#7c3aed',
//     accentTertiary: '#db2777',
//     borderColor: '#e2e8f0',
//     glassBg: 'rgba(255, 255, 255, 0.7)',
//     glassBorder: 'rgba(79, 70, 229, 0.2)',
//   };

//   const analyzer = useMemo(() => {
//     try {
//       const xMinNum = parseFloat(xMin);
//       const xMaxNum = parseFloat(xMax);
//       if (isNaN(xMinNum) || isNaN(xMaxNum)) return null;
//       return new MathAnalyzer(funcInput, [xMinNum, xMaxNum]);
//     } catch {
//       return null;
//     }
//   }, [funcInput, xMin, xMax]);

//   const analysis: AnalysisResults | null = useMemo(() => {
//     if (!analyzer || analyzer.errors.length > 0) return null;
    
//     try {
//       return {
//         criticalPoints: analyzer.findCriticalPoints(),
//         roots: analyzer.findRoots(),
//         inflectionPoints: analyzer.findInflectionPoints(),
//         undefinedValues: analyzer.findUndefinedValues(),
//         verticalAsymptotes: analyzer.findVerticalAsymptotes(),
//         horizontalAsymptote: analyzer.findHorizontalAsymptote(),
//         obliqueAsymptote: analyzer.findObliqueAsymptote(),
//       };
//     } catch {
//       return null;
//     }
//   }, [analyzer]);

//   const addTangent = () => {
//     const x = parseFloat(tangentInput);
//     if (!isNaN(x) && !tangentLines.includes(x)) {
//       setTangentLines([...tangentLines, x]);
//       setTangentInput('');
//     }
//   };

//   const removeTangent = (x: number) => {
//     setTangentLines(tangentLines.filter(t => t !== x));
//   };

//   const renderGraph = () => {
//     if (!analyzer || !analysis) {
//       return (
//         <View style={[styles.graphContainer, { backgroundColor: colors.glassBg }]}>
//           <Text style={[styles.errorText, { color: colors.textPrimary }]}>
//             {analyzer?.errors.join(', ') || 'Invalid function'}
//           </Text>
//         </View>
//       );
//     }

//     const traces: any[] = [];
//     const xMinNum = parseFloat(xMin);
//     const xMaxNum = parseFloat(xMax);
//     const yMinNum = parseFloat(yMin);
//     const yMaxNum = parseFloat(yMax);

//     // Function trace
//     if (showFunction) {
//       const points = analyzer.generatePoints();
//       traces.push({
//         x: points.x,
//         y: points.y,
//         type: 'scatter',
//         mode: 'lines',
//         name: 'f(x)',
//         line: { color: '#1f77b4', width: 3 },
//       });
//     }

//     // First derivative
//     if (showDerivative) {
//       const points = analyzer.generateDerivativePoints();
//       traces.push({
//         x: points.x,
//         y: points.y,
//         type: 'scatter',
//         mode: 'lines',
//         name: "f'(x)",
//         line: { color: '#ff7f0e', width: 2, dash: 'dash' },
//       });
//     }

//     // Second derivative
//     if (showSecondDerivative) {
//       const points = analyzer.generateSecondDerivativePoints();
//       traces.push({
//         x: points.x,
//         y: points.y,
//         type: 'scatter',
//         mode: 'lines',
//         name: "f''(x)",
//         line: { color: '#2ca02c', width: 2, dash: 'dot' },
//       });
//     }

//     // Critical points
//     if (showCritical && analysis.criticalPoints.length > 0) {
//       traces.push({
//         x: analysis.criticalPoints.map(p => p.x),
//         y: analysis.criticalPoints.map(p => p.y),
//         type: 'scatter',
//         mode: 'markers',
//         name: 'Critical Points',
//         marker: { color: '#d62728', size: 12, symbol: 'circle' },
//       });
//     }

//     // Roots
//     if (showRoots && analysis.roots.length > 0) {
//       traces.push({
//         x: analysis.roots,
//         y: analysis.roots.map(() => 0),
//         type: 'scatter',
//         mode: 'markers',
//         name: 'Roots',
//         marker: { color: '#9467bd', size: 12, symbol: 'square' },
//       });
//     }

//     // Inflection points
//     if (showInflection && analysis.inflectionPoints.length > 0) {
//       traces.push({
//         x: analysis.inflectionPoints.map(p => p.x),
//         y: analysis.inflectionPoints.map(p => p.y),
//         type: 'scatter',
//         mode: 'markers',
//         name: 'Inflection Points',
//         marker: { color: '#8c564b', size: 12, symbol: 'triangle-up' },
//       });
//     }

//     // Undefined values (holes)
//     if (showUndefined && analysis.undefinedValues.length > 0) {
//       traces.push({
//         x: analysis.undefinedValues.map(p => p.x),
//         y: analysis.undefinedValues.map(p => p.y),
//         type: 'scatter',
//         mode: 'markers',
//         name: 'Undefined (Holes)',
//         marker: {
//           color: 'white',
//           size: 14,
//           symbol: 'circle',
//           line: { color: '#ff0000', width: 3 },
//         },
//       });
//     }

//     // Vertical asymptotes
//     if (showVerticalAsymptotes) {
//       analysis.verticalAsymptotes.forEach(x => {
//         traces.push({
//           x: [x, x],
//           y: [yMinNum, yMaxNum],
//           type: 'scatter',
//           mode: 'lines',
//           name: `x = ${x.toFixed(2)}`,
//           line: { color: '#e377c2', width: 2, dash: 'dashdot' },
//           showlegend: false,
//         });
//       });
//     }

//     // Horizontal asymptote
//     if (showHorizontalAsymptote && analysis.horizontalAsymptote !== null) {
//       traces.push({
//         x: [xMinNum, xMaxNum],
//         y: [analysis.horizontalAsymptote, analysis.horizontalAsymptote],
//         type: 'scatter',
//         mode: 'lines',
//         name: `y = ${analysis.horizontalAsymptote.toFixed(2)}`,
//         line: { color: '#7f7f7f', width: 2, dash: 'dashdot' },
//       });
//     }

//     // Oblique asymptote
//     if (showObliqueAsymptote && analysis.obliqueAsymptote !== null) {
//       const { m, b } = analysis.obliqueAsymptote;
//       const x_asymp = [xMinNum, xMaxNum];
//       const y_asymp = x_asymp.map(x => m * x + b);
      
//       traces.push({
//         x: x_asymp,
//         y: y_asymp,
//         type: 'scatter',
//         mode: 'lines',
//         name: `y = ${m.toFixed(2)}x + ${b.toFixed(2)}`,
//         line: { color: '#17becf', width: 2, dash: 'dashdot' },
//       });
//     }

//     // Tangent lines
//     const tangentColors = ['#2ca02c', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f'];
//     tangentLines.forEach((x0, index) => {
//       const y0 = analyzer.evaluate(x0);

//       if (!isFinite(y0)) {
//         return;
//       }

//       // Calculate left and right derivatives using limit (MATCHING HTML VERSION)
//       const slopeLeft = analyzer.evaluateDerivativeLimit(x0, 'left');
//       const slopeRight = analyzer.evaluateDerivativeLimit(x0, 'right');

//       // Check if derivatives are different (discontinuous derivative)
//       const derivativeDiffers = Math.abs(slopeLeft - slopeRight) > 1e-6;

//       if (!isFinite(slopeLeft) && !isFinite(slopeRight)) {
//         return;
//       }

//       const extend = (xMaxNum - xMinNum) * 0.15;
//       const baseColor = tangentColors[index % tangentColors.length];

//       if (derivativeDiffers && isFinite(slopeLeft) && isFinite(slopeRight)) {
//         // Draw two different tangent lines (left and right) - MATCHING HTML VERSION

//         // Left tangent
//         const x_tangent_left = [x0 - extend, x0];
//         const y_tangent_left = x_tangent_left.map(x => y0 + slopeLeft * (x - x0));

//         traces.push({
//           x: x_tangent_left,
//           y: y_tangent_left,
//           type: 'scatter',
//           mode: 'lines',
//           name: `Left tangent at x=${x0.toFixed(2)}`,
//           line: {
//             color: baseColor,
//             width: 2.5,
//             dash: 'dot',
//           },
//         });

//         // Right tangent (slightly darker color)
//         const rgb = baseColor.match(/\w\w/g)!.map(x => parseInt(x, 16) / 255);
//         const darkerColor = `rgb(${Math.max(0, rgb[0] * 255 - 40)},${Math.max(0, rgb[1] * 255 - 40)},${Math.max(0, rgb[2] * 255 - 40)})`;

//         const x_tangent_right = [x0, x0 + extend];
//         const y_tangent_right = x_tangent_right.map(x => y0 + slopeRight * (x - x0));

//         traces.push({
//           x: x_tangent_right,
//           y: y_tangent_right,
//           type: 'scatter',
//           mode: 'lines',
//           name: `Right tangent at x=${x0.toFixed(2)}`,
//           line: {
//             color: darkerColor,
//             width: 2.5,
//             dash: 'dot',
//           },
//         });
//       } else {
//         // Draw single tangent line
//         const slope = isFinite(slopeLeft) ? slopeLeft : slopeRight;

//         if (!isFinite(slope)) {
//           return;
//         }

//         const x_tangent = [x0 - extend, x0 + extend];
//         const y_tangent = x_tangent.map(x => y0 + slope * (x - x0));

//         traces.push({
//           x: x_tangent,
//           y: y_tangent,
//           type: 'scatter',
//           mode: 'lines',
//           name: `Tangent at x=${x0.toFixed(2)}`,
//           line: {
//             color: baseColor,
//             width: 2.5,
//             dash: 'dot',
//           },
//         });
//       }

//       // Add point at tangent location
//       traces.push({
//         x: [x0],
//         y: [y0],
//         type: 'scatter',
//         mode: 'markers',
//         name: `Point at x=${x0.toFixed(2)}`,
//         marker: {
//           color: baseColor,
//           size: 10,
//           line: { color: 'black', width: 2 },
//         },
//         showlegend: false,
//       });
//     });

//     const isSmallScreen = SCREEN_WIDTH <= 768;

//     const layout = {
//       title: {
//         text: `f(x) = ${funcInput}`,
//         font: {
//           family: 'Courier',
//           size: 18,
//           color: isDark ? '#e4e8f0' : '#0f172a',
//         },
//       },
//       xaxis: {
//         title: 'x',
//         range: [xMinNum, xMaxNum],
//         gridcolor: isDark ? '#374151' : '#e2e8f0',
//         zerolinecolor: isDark ? '#6366f1' : '#4f46e5',
//         color: isDark ? '#e4e8f0' : '#0f172a',
//       },
//       yaxis: {
//         title: 'y',
//         range: [yMinNum, yMaxNum],
//         gridcolor: isDark ? '#374151' : '#e2e8f0',
//         zerolinecolor: isDark ? '#6366f1' : '#4f46e5',
//         color: isDark ? '#e4e8f0' : '#0f172a',
//       },
//       plot_bgcolor: isDark ? '#1a1f3a' : '#ffffff',
//       paper_bgcolor: isDark ? '#1a1f3a' : '#ffffff',
//       font: { color: isDark ? '#e4e8f0' : '#0f172a' },
//       showlegend: showLegend,
//       legend: {
//         bgcolor: isDark ? 'rgba(26, 31, 58, 0.8)' : 'rgba(255, 255, 255, 0.8)',
//         bordercolor: isDark ? '#6366f1' : '#4f46e5',
//         borderwidth: 1,
//         orientation: isSmallScreen ? 'h' : 'v',
//         x: isSmallScreen ? 0.5 : 1.02,
//         y: isSmallScreen ? 1.25 : 1,
//         xanchor: isSmallScreen ? 'center' : 'left',
//         yanchor: isSmallScreen ? 'top' : 'top',
//       },
//       margin: {
//         t: isSmallScreen ? 150 : 80,
//         b: 60,
//         l: 60,
//         r: isSmallScreen ? 20 : 200,
//       },
//     };

//     const config = {
//       displayModeBar: true,
//       displaylogo: false,
//       responsive: true,
//     };

//     return (
//       <View 
//         ref={graphRef}
//         style={[styles.graphContainer, { backgroundColor: colors.glassBg, borderColor: colors.glassBorder }]}
//         collapsable={false}
//       >
//         <Plotly
//           data={traces}
//           layout={layout}
//           config={config}
//           style={styles.plotlyGraph}
//         />
//       </View>
//     );
//   };

//   return (
//     <View style={[styles.container, { backgroundColor: colors.bgPrimary }]}>
//       <StatusBar barStyle={isDark ? 'light-content' : 'dark-content'} />
      
//       {/* Header with theme and legend toggles */}
//       <View style={styles.header}>
//         <View style={styles.headerContent}>
//           <Text style={[styles.title, { color: colors.accentPrimary }]}>∫ Function Grapher</Text>
//           <Text style={[styles.subtitle, { color: colors.textSecondary }]}>
//             Real-time mathematical visualization & analysis
//           </Text>
//         </View>
//         <View style={styles.headerButtons}>
//           <TouchableOpacity
//             style={[styles.headerButton, { backgroundColor: colors.glassBg, borderColor: colors.glassBorder }]}
//             onPress={handleDownloadPlot}
//           >
//             <Text style={{ fontSize: 16 }}>💾</Text>
//           </TouchableOpacity>
//           <TouchableOpacity
//             style={[styles.headerButton, { backgroundColor: colors.glassBg, borderColor: colors.glassBorder }]}
//             onPress={handleSharePlot}
//           >
//             <Text style={{ fontSize: 16 }}>📤</Text>
//           </TouchableOpacity>
//           <TouchableOpacity
//             style={[styles.headerButton, { backgroundColor: colors.glassBg, borderColor: colors.glassBorder }]}
//             onPress={() => setShowLegend(!showLegend)}
//           >
//             <Text style={{ fontSize: 16 }}>📊</Text>
//           </TouchableOpacity>
//           <TouchableOpacity
//             style={[styles.headerButton, { backgroundColor: colors.glassBg, borderColor: colors.glassBorder }]}
//             onPress={toggleTheme}
//           >
//             <Text style={{ fontSize: 16 }}>{isDark ? '🌙' : '☀️'}</Text>
//           </TouchableOpacity>
//         </View>
//       </View>

//       <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
//         {/* Input Section */}
//         <View style={[styles.section, { backgroundColor: colors.glassBg, borderColor: colors.glassBorder }]}>
//           <Text style={[styles.label, { color: colors.textSecondary }]}>FUNCTION f(x)</Text>
//           <TextInput
//             style={[styles.input, { backgroundColor: colors.bgSecondary, borderColor: colors.borderColor, color: colors.textPrimary }]}
//             value={funcInput}
//             onChangeText={setFuncInput}
//             placeholder="e.g., x^2, sin(x), (x²-1)/(x-1)"
//             placeholderTextColor={colors.textSecondary}
//           />

//           <View style={styles.rangeGrid}>
//             <View style={styles.rangeItem}>
//               <Text style={[styles.label, { color: colors.textSecondary }]}>X MIN</Text>
//               <TextInput
//                 style={[styles.inputSmall, { backgroundColor: colors.bgSecondary, borderColor: colors.borderColor, color: colors.textPrimary }]}
//                 value={xMin}
//                 onChangeText={setXMin}
//                 keyboardType="numeric"
//                 placeholderTextColor={colors.textSecondary}
//               />
//             </View>
//             <View style={styles.rangeItem}>
//               <Text style={[styles.label, { color: colors.textSecondary }]}>X MAX</Text>
//               <TextInput
//                 style={[styles.inputSmall, { backgroundColor: colors.bgSecondary, borderColor: colors.borderColor, color: colors.textPrimary }]}
//                 value={xMax}
//                 onChangeText={setXMax}
//                 keyboardType="numeric"
//                 placeholderTextColor={colors.textSecondary}
//               />
//             </View>
//             <View style={styles.rangeItem}>
//               <Text style={[styles.label, { color: colors.textSecondary }]}>Y MIN</Text>
//               <TextInput
//                 style={[styles.inputSmall, { backgroundColor: colors.bgSecondary, borderColor: colors.borderColor, color: colors.textPrimary }]}
//                 value={yMin}
//                 onChangeText={setYMin}
//                 keyboardType="numeric"
//                 placeholderTextColor={colors.textSecondary}
//               />
//             </View>
//             <View style={styles.rangeItem}>
//               <Text style={[styles.label, { color: colors.textSecondary }]}>Y MAX</Text>
//               <TextInput
//                 style={[styles.inputSmall, { backgroundColor: colors.bgSecondary, borderColor: colors.borderColor, color: colors.textPrimary }]}
//                 value={yMax}
//                 onChangeText={setYMax}
//                 keyboardType="numeric"
//                 placeholderTextColor={colors.textSecondary}
//               />
//             </View>
//           </View>

//           {/* Display Options */}
//           <View style={styles.controlsGrid}>
//             <CheckboxItem label="Function f(x)" checked={showFunction} onToggle={setShowFunction} colors={colors} color="#1f77b4" />
//             <CheckboxItem label="Derivative f'(x)" checked={showDerivative} onToggle={setShowDerivative} colors={colors} color="#ff7f0e" />
//             <CheckboxItem label="2nd Derivative" checked={showSecondDerivative} onToggle={setShowSecondDerivative} colors={colors} color="#2ca02c" />
//             <CheckboxItem label="Critical Points" checked={showCritical} onToggle={setShowCritical} colors={colors} color="#d62728" />
//             <CheckboxItem label="Roots" checked={showRoots} onToggle={setShowRoots} colors={colors} color="#9467bd" />
//             <CheckboxItem label="Inflection" checked={showInflection} onToggle={setShowInflection} colors={colors} color="#8c564b" />
//             <CheckboxItem label="Undefined" checked={showUndefined} onToggle={setShowUndefined} colors={colors} color="#ff0000" />
//             <CheckboxItem label="Vert. Asymptotes" checked={showVerticalAsymptotes} onToggle={setShowVerticalAsymptotes} colors={colors} color="#e377c2" />
//             <CheckboxItem label="Horiz. Asymptote" checked={showHorizontalAsymptote} onToggle={setShowHorizontalAsymptote} colors={colors} color="#7f7f7f" />
//             <CheckboxItem label="Oblique Asymptote" checked={showObliqueAsymptote} onToggle={setShowObliqueAsymptote} colors={colors} color="#17becf" />
//           </View>

//           {/* Tangent Lines */}
//           <View style={styles.tangentSection}>
//             <Text style={[styles.label, { color: colors.textSecondary }]}>ADD TANGENT LINE</Text>
//             <View style={styles.tangentControls}>
//               <TextInput
//                 style={[styles.inputSmall, { flex: 1, backgroundColor: colors.bgSecondary, borderColor: colors.borderColor, color: colors.textPrimary }]}
//                 value={tangentInput}
//                 onChangeText={setTangentInput}
//                 placeholder="x-coordinate"
//                 keyboardType="numeric"
//                 placeholderTextColor={colors.textSecondary}
//               />
//               <TouchableOpacity
//                 style={[styles.button, { backgroundColor: colors.accentPrimary }]}
//                 onPress={addTangent}
//               >
//                 <Text style={styles.buttonText}>Add</Text>
//               </TouchableOpacity>
//             </View>
//             <View style={styles.tangentList}>
//               {tangentLines.map((x, idx) => (
//                 <View key={idx} style={[styles.tangentTag, { backgroundColor: colors.bgTertiary, borderColor: colors.borderColor }]}>
//                   <Text style={[styles.tangentTagText, { color: colors.textPrimary }]}>
//                     x = {x.toFixed(2)}
//                   </Text>
//                   <TouchableOpacity onPress={() => removeTangent(x)}>
//                     <Text style={styles.removeButton}>×</Text>
//                   </TouchableOpacity>
//                 </View>
//               ))}
//             </View>
//           </View>
//         </View>

//         {/* Graph */}
//         {renderGraph()}

//         {/* Analysis */}
//         {analysis && (
//           <View style={[styles.section, { backgroundColor: colors.glassBg, borderColor: colors.glassBorder }]}>
//             <Text style={[styles.sectionTitle, { color: colors.textPrimary }]}>Mathematical Analysis</Text>
            
//             <AnalysisCard
//               title="Function Expressions"
//               content={`f(x) = ${funcInput}\nf'(x) = ${analyzer?.derivNode.toString()}\nf''(x) = ${analyzer?.secondDerivNode.toString()}`}
//               colors={colors}
//             />

//             <AnalysisCard
//               title={`Critical Points (${analysis.criticalPoints.length})`}
//               content={analysis.criticalPoints.length > 0
//                 ? analysis.criticalPoints.map(p => `(${p.x.toFixed(4)}, ${p.y.toFixed(4)})`).join('\n')
//                 : 'None found'}
//               colors={colors}
//             />

//             <AnalysisCard
//               title={`Roots/Zeros (${analysis.roots.length})`}
//               content={analysis.roots.length > 0
//                 ? analysis.roots.map(r => `x = ${r.toFixed(4)}`).join('\n')
//                 : 'None found'}
//               colors={colors}
//             />

//             <AnalysisCard
//               title={`Inflection Points (${analysis.inflectionPoints.length})`}
//               content={analysis.inflectionPoints.length > 0
//                 ? analysis.inflectionPoints.map(p => `(${p.x.toFixed(4)}, ${p.y.toFixed(4)})`).join('\n')
//                 : 'None found'}
//               colors={colors}
//             />

//             <AnalysisCard
//               title={`Undefined Values (Holes) (${analysis.undefinedValues.length})`}
//               content={analysis.undefinedValues.length > 0
//                 ? analysis.undefinedValues.map(p => `x = ${p.x.toFixed(4)}, limit = ${p.y.toFixed(4)}`).join('\n')
//                 : 'None found'}
//               colors={colors}
//             />

//             <AnalysisCard
//               title="Asymptotes"
//               content={[
//                 analysis.verticalAsymptotes.length > 0 ? `Vertical:\n${analysis.verticalAsymptotes.map(a => `x = ${a.toFixed(4)}`).join('\n')}` : '',
//                 analysis.horizontalAsymptote !== null ? `Horizontal:\ny = ${analysis.horizontalAsymptote.toFixed(4)}` : '',
//                 analysis.obliqueAsymptote !== null ? `Oblique:\ny = ${analysis.obliqueAsymptote.m.toFixed(4)}x + ${analysis.obliqueAsymptote.b.toFixed(4)}` : ''
//               ].filter(Boolean).join('\n\n') || 'None found'}
//               colors={colors}
//             />

//             <AnalysisCard
//               title="Domain"
//               content={`All real numbers ℝ\n(computed over [${xMin}, ${xMax}])`}
//               colors={colors}
//             />
//           </View>
//         )}
//       </ScrollView>
//     </View>
//   );
// }

// const styles = StyleSheet.create({
//   container: {
//     flex: 1,
//     paddingTop: Platform.OS === 'ios' ? 50 : StatusBar.currentHeight || 0,
//   },
//   scrollView: {
//     flex: 1,
//   },
//   header: {
//     flexDirection: 'row',
//     justifyContent: 'space-between',
//     alignItems: 'center',
//     paddingHorizontal: 20,
//     paddingVertical: 20,
//   },
//   headerContent: {
//     flex: 1,
//   },
//   headerButtons: {
//     flexDirection: 'row',
//     gap: 10,
//   },
//   headerButton: {
//     width: 44,
//     height: 44,
//     borderRadius: 22,
//     borderWidth: 1,
//     justifyContent: 'center',
//     alignItems: 'center',
//   },
//   title: {
//     fontSize: 28,
//     fontWeight: '700',
//     marginBottom: 4,
//     fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
//   },
//   subtitle: {
//     fontSize: 12,
//     fontWeight: '400',
//     fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
//   },
//   section: {
//     marginHorizontal: 20,
//     marginBottom: 20,
//     padding: 20,
//     borderRadius: 20,
//     borderWidth: 1,
//   },
//   label: {
//     fontSize: 12,
//     fontWeight: '600',
//     marginBottom: 8,
//     textTransform: 'uppercase',
//     letterSpacing: 0.5,
//     fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
//   },
//   input: {
//     width: '100%',
//     padding: 16,
//     borderRadius: 12,
//     borderWidth: 2,
//     fontSize: 16,
//     fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
//     marginBottom: 16,
//   },
//   inputSmall: {
//     padding: 12,
//     borderRadius: 12,
//     borderWidth: 2,
//     fontSize: 14,
//     fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
//   },
//   rangeGrid: {
//     flexDirection: 'row',
//     flexWrap: 'wrap',
//     gap: 12,
//     marginBottom: 16,
//   },
//   rangeItem: {
//     flex: 1,
//     minWidth: 150,
//   },
//   controlsGrid: {
//     marginTop: 16,
//     gap: 8,
//   },
//   controlItem: {
//     flexDirection: 'row',
//     alignItems: 'center',
//     padding: 12,
//     borderRadius: 12,
//     borderWidth: 2,
//     gap: 12,
//   },
//   checkbox: {
//     width: 20,
//     height: 20,
//     borderRadius: 6,
//     borderWidth: 2,
//     justifyContent: 'center',
//     alignItems: 'center',
//   },
//   checkmark: {
//     color: 'white',
//     fontSize: 14,
//     fontWeight: 'bold',
//   },
//   controlLabel: {
//     flex: 1,
//     fontSize: 14,
//     fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
//   },
//   colorIndicator: {
//     width: 12,
//     height: 12,
//     borderRadius: 6,
//   },
//   tangentSection: {
//     marginTop: 16,
//     paddingTop: 16,
//     borderTopWidth: 1,
//   },
//   tangentControls: {
//     flexDirection: 'row',
//     gap: 12,
//     marginBottom: 12,
//   },
//   button: {
//     paddingHorizontal: 24,
//     paddingVertical: 12,
//     borderRadius: 12,
//     justifyContent: 'center',
//     alignItems: 'center',
//   },
//   buttonText: {
//     color: 'white',
//     fontSize: 14,
//     fontWeight: '600',
//     textTransform: 'uppercase',
//     fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
//   },
//   tangentList: {
//     flexDirection: 'row',
//     flexWrap: 'wrap',
//     gap: 8,
//   },
//   tangentTag: {
//     flexDirection: 'row',
//     alignItems: 'center',
//     padding: 8,
//     borderRadius: 20,
//     borderWidth: 1,
//     gap: 8,
//   },
//   tangentTagText: {
//     fontSize: 12,
//     fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
//   },
//   removeButton: {
//     fontSize: 20,
//     color: '#ef4444',
//   },
//   graphContainer: {
//     marginHorizontal: 20,
//     marginBottom: 20,
//     padding: 20,
//     borderRadius: 20,
//     borderWidth: 1,
//     position: 'relative',
//     height: GRAPH_HEIGHT + 80, // Account for padding
//   },
//   plotlyGraph: {
//     flex: 1,
//     width: '100%',
//   },
//   errorText: {
//     fontSize: 14,
//     fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
//     textAlign: 'center',
//     padding: 20,
//   },
//   sectionTitle: {
//     fontSize: 20,
//     fontWeight: '600',
//     marginBottom: 16,
//     fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
//   },
//   analysisCard: {
//     backgroundColor: '#1a1f3a',
//     borderRadius: 12,
//     padding: 16,
//     marginBottom: 12,
//     borderLeftWidth: 4,
//   },
//   analysisCardTitle: {
//     fontSize: 14,
//     fontWeight: '600',
//     marginBottom: 8,
//     textTransform: 'uppercase',
//     fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
//   },
//   analysisCardContent: {
//     fontSize: 13,
//     lineHeight: 20,
//     fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
//   },
// });


import React, { useState, useEffect, useMemo, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
  useColorScheme,
  Platform,
  StatusBar,
  Animated,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Plotly from 'react-native-plotly';
import * as math from 'mathjs';
import { captureRef } from 'react-native-view-shot';
import * as Sharing from 'expo-sharing';
import * as MediaLibrary from 'expo-media-library';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');
const GRAPH_WIDTH = SCREEN_WIDTH - 40;
const GRAPH_HEIGHT = 300;

// Types
interface Point {
  x: number;
  y: number;
}

interface AsymptoteOblique {
  m: number;
  b: number;
}

interface AnalysisResults {
  criticalPoints: Point[];
  roots: number[];
  inflectionPoints: Point[];
  undefinedValues: Point[];
  verticalAsymptotes: number[];
  horizontalAsymptote: number | null;
  obliqueAsymptote: AsymptoteOblique | null;
}

// Toast Component
function Toast({ message, type, visible, onHide }: { message: string; type: 'success' | 'error' | 'info'; visible: boolean; onHide: () => void }) {
  const opacity = useRef(new Animated.Value(0)).current;
  const translateY = useRef(new Animated.Value(-20)).current;

  useEffect(() => {
    if (visible) {
      Animated.parallel([
        Animated.timing(opacity, {
          toValue: 1,
          duration: 300,
          useNativeDriver: true,
        }),
        Animated.timing(translateY, {
          toValue: 0,
          duration: 300,
          useNativeDriver: true,
        }),
      ]).start();

      const timer = setTimeout(() => {
        Animated.parallel([
          Animated.timing(opacity, {
            toValue: 0,
            duration: 300,
            useNativeDriver: true,
          }),
          Animated.timing(translateY, {
            toValue: -20,
            duration: 300,
            useNativeDriver: true,
          }),
        ]).start(() => onHide());
      }, 3000);

      return () => clearTimeout(timer);
    }
  }, [visible]);

  if (!visible) return null;

  const bgColor = type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6';

  return (
    <Animated.View
      style={[
        styles.toast,
        {
          opacity,
          transform: [{ translateY }],
          backgroundColor: bgColor,
        },
      ]}
    >
      <Text style={styles.toastText}>{message}</Text>
    </Animated.View>
  );
}

// Math Analyzer Class - Keep this EXACTLY the same as HTML version
class MathAnalyzer {
  funcStr: string;
  xRange: [number, number];
  numPoints: number;
  node: any;
  func: any;
  funcOriginal: any;
  derivNode: any;
  deriv: any;
  secondDerivNode: any;
  secondDeriv: any;
  errors: string[];

  constructor(funcStr: string, xRange: [number, number], numPoints = 1000) {
    this.funcStr = this.normalizeFunction(funcStr);
    this.xRange = xRange;
    this.numPoints = numPoints;
    this.errors = [];

    try {
      this.node = math.parse(this.funcStr);
      this.func = this.node.compile();

      // Keep original for undefined detection
      this.funcOriginal = this.func;

      this.derivNode = math.derivative(this.node, 'x');
      this.deriv = this.derivNode.compile();
      this.secondDerivNode = math.derivative(this.derivNode, 'x');
      this.secondDeriv = this.secondDerivNode.compile();
    } catch (e: any) {
      this.errors.push(`Parse error: ${e.message}`);
    }
  }

  normalizeFunction(input: string): string {
    let normalized = input;
    normalized = normalized.replace(/²/g, '^2');
    normalized = normalized.replace(/³/g, '^3');
    normalized = normalized.replace(/⁴/g, '^4');
    normalized = normalized.replace(/⁵/g, '^5');
    normalized = normalized.replace(/⁶/g, '^6');
    normalized = normalized.replace(/\*\*/g, '^');

    const openParen = (normalized.match(/\(/g) || []).length;
    const closeParen = (normalized.match(/\)/g) || []).length;
    if (openParen > closeParen) {
      normalized += ')'.repeat(openParen - closeParen);
    }

    const openSquare = (normalized.match(/\[/g) || []).length;
    const closeSquare = (normalized.match(/\]/g) || []).length;
    if (openSquare > closeSquare) {
      normalized += ']'.repeat(openSquare - closeSquare);
    }

    normalized = normalized.replace(/sqrt/gi, 'sqrt');
    normalized = normalized.replace(/abs/gi, 'abs');

    return normalized;
  }

  evaluate(x: number): number {
    try {
      const result = this.func.evaluate({ x });
      return isFinite(result) ? result : NaN;
    } catch {
      return NaN;
    }
  }

  evaluateDerivative(x: number): number {
    try {
      const result = this.deriv.evaluate({ x });
      return isFinite(result) ? result : NaN;
    } catch {
      return NaN;
    }
  }

  evaluateSecondDerivative(x: number): number {
    try {
      const result = this.secondDeriv.evaluate({ x });
      return isFinite(result) ? result : NaN;
    } catch {
      return NaN;
    }
  }

  evaluateDerivativeLimit(x: number, direction: 'left' | 'right' | 'both' = 'both'): number {
    const h = 1e-7;
    if (direction === 'left') {
      const f_x = this.evaluate(x);
      const f_x_h = this.evaluate(x - h);
      return (f_x - f_x_h) / h;
    } else if (direction === 'right') {
      const f_x = this.evaluate(x);
      const f_x_h = this.evaluate(x + h);
      return (f_x_h - f_x) / h;
    } else {
      const f_x_h = this.evaluate(x + h);
      const f_x_h_neg = this.evaluate(x - h);
      return (f_x_h - f_x_h_neg) / (2 * h);
    }
  }

  generatePoints(): { x: number[], y: number[] } {
    const [xMin, xMax] = this.xRange;
    const step = (xMax - xMin) / this.numPoints;
    const x: number[] = [];
    const y: number[] = [];

    for (let i = 0; i <= this.numPoints; i++) {
      const xVal = xMin + i * step;
      const yVal = this.evaluate(xVal);
      x.push(xVal);
      y.push(yVal);
    }

    return { x, y };
  }

  generateDerivativePoints(): { x: number[], y: number[] } {
    const [xMin, xMax] = this.xRange;
    const step = (xMax - xMin) / this.numPoints;
    const x: number[] = [];
    const y: number[] = [];

    for (let i = 0; i <= this.numPoints; i++) {
      const xVal = xMin + i * step;
      const yVal = this.evaluateDerivative(xVal);
      x.push(xVal);
      y.push(yVal);
    }

    return { x, y };
  }

  generateSecondDerivativePoints(): { x: number[], y: number[] } {
    const [xMin, xMax] = this.xRange;
    const step = (xMax - xMin) / this.numPoints;
    const x: number[] = [];
    const y: number[] = [];

    for (let i = 0; i <= this.numPoints; i++) {
      const xVal = xMin + i * step;
      const yVal = this.evaluateSecondDerivative(xVal);
      x.push(xVal);
      y.push(yVal);
    }

    return { x, y };
  }

  bisectionMethod(a: number, b: number, tolerance = 0.0001, maxIter = 50): number | null {
    let fa = this.evaluate(a);
    let fb = this.evaluate(b);

    if (fa * fb > 0) return null;

    for (let i = 0; i < maxIter; i++) {
      const c = (a + b) / 2;
      const fc = this.evaluate(c);

      if (Math.abs(fc) < tolerance || (b - a) / 2 < tolerance) {
        return c;
      }

      if (fa * fc < 0) {
        b = c;
        fb = fc;
      } else {
        a = c;
        fa = fc;
      }
    }

    return (a + b) / 2;
  }

  findRoots(): number[] {
    const [xMin, xMax] = this.xRange;
    const step = (xMax - xMin) / 1000;
    const roots: number[] = [];
    let prevY = this.evaluate(xMin);

    for (let x = xMin + step; x <= xMax; x += step) {
      const y = this.evaluate(x);
      if (!isNaN(y) && !isNaN(prevY)) {
        if (prevY * y < 0 || Math.abs(y) < 0.001) {
          const root = this.bisectionMethod(x - step, x);
          if (root !== null && !roots.some((r) => Math.abs(r - root) < 0.01)) {
            roots.push(root);
          }
        }
      }
      prevY = y;
    }

    return roots;
  }

  bisectionDerivative(a: number, b: number, tolerance = 0.0001, maxIter = 50): number | null {
    let fa = this.evaluateDerivative(a);
    let fb = this.evaluateDerivative(b);

    if (fa * fb > 0) return null;

    for (let i = 0; i < maxIter; i++) {
      const c = (a + b) / 2;
      const fc = this.evaluateDerivative(c);

      if (Math.abs(fc) < tolerance || (b - a) / 2 < tolerance) {
        return c;
      }

      if (fa * fc < 0) {
        b = c;
        fb = fc;
      } else {
        a = c;
        fa = fc;
      }
    }

    return (a + b) / 2;
  }

  findCriticalPoints(): Point[] {
    const [xMin, xMax] = this.xRange;
    const step = (xMax - xMin) / 1000;
    const criticalPoints: Point[] = [];
    let prevDy = this.evaluateDerivative(xMin);

    for (let x = xMin + step; x <= xMax; x += step) {
      const dy = this.evaluateDerivative(x);
      if (!isNaN(dy) && !isNaN(prevDy)) {
        if (prevDy * dy < 0 || Math.abs(dy) < 0.001) {
          const critX = this.bisectionDerivative(x - step, x);
          if (critX !== null && !criticalPoints.some((p) => Math.abs(p.x - critX) < 0.01)) {
            const critY = this.evaluate(critX);
            if (!isNaN(critY)) {
              criticalPoints.push({ x: critX, y: critY });
            }
          }
        }
      }
      prevDy = dy;
    }

    return criticalPoints;
  }

  bisectionSecondDerivative(a: number, b: number, tolerance = 0.0001, maxIter = 50): number | null {
    let fa = this.evaluateSecondDerivative(a);
    let fb = this.evaluateSecondDerivative(b);

    if (fa * fb > 0) return null;

    for (let i = 0; i < maxIter; i++) {
      const c = (a + b) / 2;
      const fc = this.evaluateSecondDerivative(c);

      if (Math.abs(fc) < tolerance || (b - a) / 2 < tolerance) {
        return c;
      }

      if (fa * fc < 0) {
        b = c;
        fb = fc;
      } else {
        a = c;
        fa = fc;
      }
    }

    return (a + b) / 2;
  }

  findInflectionPoints(): Point[] {
    const [xMin, xMax] = this.xRange;
    const step = (xMax - xMin) / 1000;
    const inflectionPoints: Point[] = [];
    let prevDdy = this.evaluateSecondDerivative(xMin);

    for (let x = xMin + step; x <= xMax; x += step) {
      const ddy = this.evaluateSecondDerivative(x);
      if (!isNaN(ddy) && !isNaN(prevDdy)) {
        if (prevDdy * ddy < 0 || Math.abs(ddy) < 0.001) {
          const inflX = this.bisectionSecondDerivative(x - step, x);
          if (inflX !== null && !inflectionPoints.some((p) => Math.abs(p.x - inflX) < 0.01)) {
            const inflY = this.evaluate(inflX);
            if (!isNaN(inflY)) {
              inflectionPoints.push({ x: inflX, y: inflY });
            }
          }
        }
      }
      prevDdy = ddy;
    }

    return inflectionPoints;
  }

  findUndefinedValues(): Point[] {
    const [xMin, xMax] = this.xRange;
    const undefined: Point[] = [];

    if (!this.funcStr.includes('/')) {
      return [];
    }

    const step = (xMax - xMin) / 1000;

    for (let x = xMin; x <= xMax; x += step) {
      const y = this.evaluate(x);

      if (isNaN(y) || !isFinite(y)) {
        const h = 0.0001;
        const leftVal = this.evaluate(x - h);
        const rightVal = this.evaluate(x + h);

        if (isFinite(leftVal) && isFinite(rightVal) && Math.abs(leftVal - rightVal) < 0.01) {
          const limitVal = (leftVal + rightVal) / 2;

          if (!undefined.some((p) => Math.abs(p.x - x) < step * 2)) {
            undefined.push({ x, y: limitVal });
          }
        }
      }
    }

    return undefined;
  }

  findVerticalAsymptotes(): number[] {
    const [xMin, xMax] = this.xRange;
    const step = (xMax - xMin) / 1000;
    const asymptotes: number[] = [];
    let prevY = this.evaluate(xMin);

    for (let x = xMin + step; x <= xMax; x += step) {
      const y = this.evaluate(x);

      if ((isFinite(prevY) && !isFinite(y)) || (!isFinite(prevY) && isFinite(y))) {
        const h = 0.0001;
        const leftVal = this.evaluate(x - h);
        const rightVal = this.evaluate(x + h);

        if (!isFinite(leftVal) || !isFinite(rightVal) || Math.abs(leftVal - rightVal) > 10) {
          if (!asymptotes.some((a) => Math.abs(a - x) < step * 2)) {
            asymptotes.push(x);
          }
        }
      } else if (isFinite(prevY) && isFinite(y) && Math.abs(y - prevY) > 1000) {
        if (!asymptotes.some((a) => Math.abs(a - x) < step * 2)) {
          asymptotes.push(x);
        }
      }

      prevY = y;
    }

    return asymptotes;
  }

  findHorizontalAsymptote(): number | null {
    const farRight = this.evaluate(this.xRange[1] * 10);
    const farLeft = this.evaluate(this.xRange[0] * 10);

    if (isFinite(farRight) && isFinite(farLeft) && Math.abs(farRight - farLeft) < 0.1) {
      return (farRight + farLeft) / 2;
    }

    return null;
  }

  findObliqueAsymptote(): AsymptoteOblique | null {
    if (this.findHorizontalAsymptote() !== null) {
      return null;
    }

    const [xMin, xMax] = this.xRange;
    const xLarge = Math.max(Math.abs(xMin), Math.abs(xMax)) * 10;

    const f_pos = this.evaluate(xLarge);
    const f_neg = this.evaluate(-xLarge);

    if (!isFinite(f_pos) || !isFinite(f_neg)) {
      return null;
    }

    const m_pos = f_pos / xLarge;
    const m_neg = f_neg / -xLarge;

    if (!isFinite(m_pos) || !isFinite(m_neg) || Math.abs(m_pos) < 0.001 || Math.abs(m_neg) < 0.001) {
      return null;
    }

    if (Math.abs(m_pos - m_neg) > 0.1) {
      return null;
    }

    const m = (m_pos + m_neg) / 2;
    const b_pos = f_pos - m * xLarge;
    const b_neg = f_neg - m * -xLarge;

    if (!isFinite(b_pos) || !isFinite(b_neg)) {
      return null;
    }

    if (Math.abs(b_pos - b_neg) > 1) {
      return null;
    }

    const b = (b_pos + b_neg) / 2;

    return { m, b };
  }
}

// Checkbox Component
function CheckboxItem({ 
  label, 
  checked, 
  onToggle, 
  colors, 
  color 
}: { 
  label: string; 
  checked: boolean; 
  onToggle: (val: boolean) => void; 
  colors: any; 
  color: string;
}) {
  return (
    <TouchableOpacity
      style={[styles.controlItem, { backgroundColor: colors.bgSecondary, borderColor: colors.borderColor }]}
      onPress={() => onToggle(!checked)}
    >
      <View style={[styles.checkbox, { borderColor: colors.borderColor, backgroundColor: checked ? colors.accentPrimary : 'transparent' }]}>
        {checked && <Text style={styles.checkmark}>✓</Text>}
      </View>
      <Text style={[styles.controlLabel, { color: colors.textPrimary }]}>{label}</Text>
      <View style={[styles.colorIndicator, { backgroundColor: color }]} />
    </TouchableOpacity>
  );
}

// Analysis Card Component
function AnalysisCard({ 
  title, 
  content, 
  colors 
}: { 
  title: string; 
  content: string; 
  colors: any;
}) {
  return (
    <View style={[styles.analysisCard, { backgroundColor: colors.bgSecondary, borderLeftColor: colors.accentPrimary }]}>
      <Text style={[styles.analysisCardTitle, { color: colors.accentPrimary }]}>{title}</Text>
      <Text style={[styles.analysisCardContent, { color: colors.textPrimary }]}>{content}</Text>
    </View>
  );
}

// Main App Component
export default function FunctionGrapher() {
  const systemColorScheme = useColorScheme();
  const [isDark, setIsDark] = useState(systemColorScheme === 'dark');
  const [showLegend, setShowLegend] = useState(true);
  const [funcInput, setFuncInput] = useState('x^2');
  const [xMin, setXMin] = useState('-10');
  const [xMax, setXMax] = useState('10');
  const [yMin, setYMin] = useState('-10');
  const [yMax, setYMax] = useState('10');
  const [showFunction, setShowFunction] = useState(true);
  const [showDerivative, setShowDerivative] = useState(true);
  const [showSecondDerivative, setShowSecondDerivative] = useState(false);
  const [showCritical, setShowCritical] = useState(true);
  const [showRoots, setShowRoots] = useState(true);
  const [showInflection, setShowInflection] = useState(false);
  const [showUndefined, setShowUndefined] = useState(true);
  const [showVerticalAsymptotes, setShowVerticalAsymptotes] = useState(true);
  const [showHorizontalAsymptote, setShowHorizontalAsymptote] = useState(false);
  const [showObliqueAsymptote, setShowObliqueAsymptote] = useState(false);
  const [tangentInput, setTangentInput] = useState('');
  const [tangentLines, setTangentLines] = useState<number[]>([]);
  const graphRef = useRef<View>(null);
  
  // Toast state
  const [toast, setToast] = useState({ visible: false, message: '', type: 'info' as 'success' | 'error' | 'info' });

  const showToast = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
    setToast({ visible: true, message, type });
  };

  const hideToast = () => {
    setToast({ ...toast, visible: false });
  };

  // Load theme from AsyncStorage on mount
  useEffect(() => {
    loadTheme();
  }, []);

  const loadTheme = async () => {
    try {
      const savedTheme = await AsyncStorage.getItem('math-grapher-theme');
      if (savedTheme) {
        setIsDark(savedTheme === 'dark');
      }
    } catch (error) {
      console.log('Error loading theme:', error);
    }
  };

  const toggleTheme = async () => {
    const newTheme = !isDark;
    setIsDark(newTheme);
    try {
      await AsyncStorage.setItem('math-grapher-theme', newTheme ? 'dark' : 'light');
    } catch (error) {
      console.log('Error saving theme:', error);
    }
  };

  const handleDownloadPlot = async () => {
    try {
      if (!graphRef.current) {
        showToast('Graph not ready', 'error');
        return;
      }

      // Request permissions
      const { status } = await MediaLibrary.requestPermissionsAsync();
      if (status !== 'granted') {
        showToast('Permission denied to save images', 'error');
        return;
      }

      // Capture the graph view as image
      const uri = await captureRef(graphRef, {
        format: 'png',
        quality: 1,
        result: 'tmpfile',
      });

      // Save directly to media library
      const asset = await MediaLibrary.createAssetAsync(uri);
      await MediaLibrary.createAlbumAsync('Function Grapher', asset, false);
      
      showToast('Plot saved to gallery', 'success');
    } catch (error) {
      console.error('Error saving plot:', error);
      showToast('Failed to save plot', 'error');
    }
  };

  const handleSharePlot = async () => {
    try {
      if (!graphRef.current) {
        showToast('Graph not ready', 'error');
        return;
      }

      // Capture the graph view as image
      const uri = await captureRef(graphRef, {
        format: 'png',
        quality: 1,
        result: 'tmpfile',
      });

      // Share directly
      const sharingAvailable = await Sharing.isAvailableAsync();
      if (sharingAvailable) {
        await Sharing.shareAsync(uri, {
          mimeType: 'image/png',
          dialogTitle: 'Share Plot',
        });
      } else {
        showToast('Sharing not available', 'info');
      }
    } catch (error) {
      console.error('Error sharing plot:', error);
      showToast('Failed to share plot', 'error');
    }
  };

  const colors = isDark ? {
    bgPrimary: '#0a0e27',
    bgSecondary: '#1a1f3a',
    bgTertiary: '#252b4a',
    textPrimary: '#e4e8f0',
    textSecondary: '#9ca3af',
    accentPrimary: '#6366f1',
    accentSecondary: '#8b5cf6',
    accentTertiary: '#ec4899',
    borderColor: '#374151',
    glassBg: 'rgba(26, 31, 58, 0.7)',
    glassBorder: 'rgba(99, 102, 241, 0.2)',
  } : {
    bgPrimary: '#f8fafc',
    bgSecondary: '#ffffff',
    bgTertiary: '#f1f5f9',
    textPrimary: '#0f172a',
    textSecondary: '#64748b',
    accentPrimary: '#4f46e5',
    accentSecondary: '#7c3aed',
    accentTertiary: '#db2777',
    borderColor: '#e2e8f0',
    glassBg: 'rgba(255, 255, 255, 0.7)',
    glassBorder: 'rgba(79, 70, 229, 0.2)',
  };

  const analyzer = useMemo(() => {
    try {
      const xMinNum = parseFloat(xMin);
      const xMaxNum = parseFloat(xMax);
      if (isNaN(xMinNum) || isNaN(xMaxNum)) return null;
      return new MathAnalyzer(funcInput, [xMinNum, xMaxNum]);
    } catch {
      return null;
    }
  }, [funcInput, xMin, xMax]);

  const analysis: AnalysisResults | null = useMemo(() => {
    if (!analyzer || analyzer.errors.length > 0) return null;
    
    try {
      return {
        criticalPoints: analyzer.findCriticalPoints(),
        roots: analyzer.findRoots(),
        inflectionPoints: analyzer.findInflectionPoints(),
        undefinedValues: analyzer.findUndefinedValues(),
        verticalAsymptotes: analyzer.findVerticalAsymptotes(),
        horizontalAsymptote: analyzer.findHorizontalAsymptote(),
        obliqueAsymptote: analyzer.findObliqueAsymptote(),
      };
    } catch {
      return null;
    }
  }, [analyzer]);

  const addTangent = () => {
    const x = parseFloat(tangentInput);
    if (!isNaN(x) && !tangentLines.includes(x)) {
      setTangentLines([...tangentLines, x]);
      setTangentInput('');
      showToast('Tangent line added', 'success');
    }
  };

  const removeTangent = (x: number) => {
    setTangentLines(tangentLines.filter(t => t !== x));
    showToast('Tangent line removed', 'info');
  };

  const renderGraph = () => {
    if (!analyzer || !analysis) {
      return (
        <View style={[styles.graphContainer, { backgroundColor: colors.glassBg }]}>
          <Text style={[styles.errorText, { color: colors.textPrimary }]}>
            {analyzer?.errors.join(', ') || 'Invalid function'}
          </Text>
        </View>
      );
    }

    const traces: any[] = [];
    const xMinNum = parseFloat(xMin);
    const xMaxNum = parseFloat(xMax);
    const yMinNum = parseFloat(yMin);
    const yMaxNum = parseFloat(yMax);

    // Function trace
    if (showFunction) {
      const points = analyzer.generatePoints();
      traces.push({
        x: points.x,
        y: points.y,
        type: 'scatter',
        mode: 'lines',
        name: 'f(x)',
        line: { color: '#1f77b4', width: 3 },
      });
    }

    // First derivative
    if (showDerivative) {
      const points = analyzer.generateDerivativePoints();
      traces.push({
        x: points.x,
        y: points.y,
        type: 'scatter',
        mode: 'lines',
        name: "f'(x)",
        line: { color: '#ff7f0e', width: 2, dash: 'dash' },
      });
    }

    // Second derivative
    if (showSecondDerivative) {
      const points = analyzer.generateSecondDerivativePoints();
      traces.push({
        x: points.x,
        y: points.y,
        type: 'scatter',
        mode: 'lines',
        name: "f''(x)",
        line: { color: '#2ca02c', width: 2, dash: 'dot' },
      });
    }

    // Critical points
    if (showCritical && analysis.criticalPoints.length > 0) {
      traces.push({
        x: analysis.criticalPoints.map(p => p.x),
        y: analysis.criticalPoints.map(p => p.y),
        type: 'scatter',
        mode: 'markers',
        name: 'Critical Points',
        marker: { color: '#d62728', size: 12, symbol: 'circle' },
      });
    }

    // Roots
    if (showRoots && analysis.roots.length > 0) {
      traces.push({
        x: analysis.roots,
        y: analysis.roots.map(() => 0),
        type: 'scatter',
        mode: 'markers',
        name: 'Roots',
        marker: { color: '#9467bd', size: 12, symbol: 'square' },
      });
    }

    // Inflection points
    if (showInflection && analysis.inflectionPoints.length > 0) {
      traces.push({
        x: analysis.inflectionPoints.map(p => p.x),
        y: analysis.inflectionPoints.map(p => p.y),
        type: 'scatter',
        mode: 'markers',
        name: 'Inflection Points',
        marker: { color: '#8c564b', size: 12, symbol: 'triangle-up' },
      });
    }

    // Undefined values (holes)
    if (showUndefined && analysis.undefinedValues.length > 0) {
      traces.push({
        x: analysis.undefinedValues.map(p => p.x),
        y: analysis.undefinedValues.map(p => p.y),
        type: 'scatter',
        mode: 'markers',
        name: 'Undefined (Holes)',
        marker: {
          color: 'white',
          size: 14,
          symbol: 'circle',
          line: { color: '#ff0000', width: 3 },
        },
      });
    }

    // Vertical asymptotes
    if (showVerticalAsymptotes) {
      analysis.verticalAsymptotes.forEach(x => {
        traces.push({
          x: [x, x],
          y: [yMinNum, yMaxNum],
          type: 'scatter',
          mode: 'lines',
          name: `x = ${x.toFixed(2)}`,
          line: { color: '#e377c2', width: 2, dash: 'dashdot' },
          showlegend: false,
        });
      });
    }

    // Horizontal asymptote
    if (showHorizontalAsymptote && analysis.horizontalAsymptote !== null) {
      traces.push({
        x: [xMinNum, xMaxNum],
        y: [analysis.horizontalAsymptote, analysis.horizontalAsymptote],
        type: 'scatter',
        mode: 'lines',
        name: `y = ${analysis.horizontalAsymptote.toFixed(2)}`,
        line: { color: '#7f7f7f', width: 2, dash: 'dashdot' },
      });
    }

    // Oblique asymptote
    if (showObliqueAsymptote && analysis.obliqueAsymptote !== null) {
      const { m, b } = analysis.obliqueAsymptote;
      const x_asymp = [xMinNum, xMaxNum];
      const y_asymp = x_asymp.map(x => m * x + b);
      
      traces.push({
        x: x_asymp,
        y: y_asymp,
        type: 'scatter',
        mode: 'lines',
        name: `y = ${m.toFixed(2)}x + ${b.toFixed(2)}`,
        line: { color: '#17becf', width: 2, dash: 'dashdot' },
      });
    }

    // Tangent lines
    const tangentColors = ['#2ca02c', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f'];
    tangentLines.forEach((x0, index) => {
      const y0 = analyzer.evaluate(x0);

      if (!isFinite(y0)) {
        return;
      }

      // Calculate left and right derivatives using limit (MATCHING HTML VERSION)
      const slopeLeft = analyzer.evaluateDerivativeLimit(x0, 'left');
      const slopeRight = analyzer.evaluateDerivativeLimit(x0, 'right');

      // Check if derivatives are different (discontinuous derivative)
      const derivativeDiffers = Math.abs(slopeLeft - slopeRight) > 1e-6;

      if (!isFinite(slopeLeft) && !isFinite(slopeRight)) {
        return;
      }

      const extend = (xMaxNum - xMinNum) * 0.15;
      const baseColor = tangentColors[index % tangentColors.length];

      if (derivativeDiffers && isFinite(slopeLeft) && isFinite(slopeRight)) {
        // Draw two different tangent lines (left and right) - MATCHING HTML VERSION

        // Left tangent
        const x_tangent_left = [x0 - extend, x0];
        const y_tangent_left = x_tangent_left.map(x => y0 + slopeLeft * (x - x0));

        traces.push({
          x: x_tangent_left,
          y: y_tangent_left,
          type: 'scatter',
          mode: 'lines',
          name: `Left tangent at x=${x0.toFixed(2)}`,
          line: {
            color: baseColor,
            width: 2.5,
            dash: 'dot',
          },
        });

        // Right tangent (slightly darker color)
        const rgb = baseColor.match(/\w\w/g)!.map(x => parseInt(x, 16) / 255);
        const darkerColor = `rgb(${Math.max(0, rgb[0] * 255 - 40)},${Math.max(0, rgb[1] * 255 - 40)},${Math.max(0, rgb[2] * 255 - 40)})`;

        const x_tangent_right = [x0, x0 + extend];
        const y_tangent_right = x_tangent_right.map(x => y0 + slopeRight * (x - x0));

        traces.push({
          x: x_tangent_right,
          y: y_tangent_right,
          type: 'scatter',
          mode: 'lines',
          name: `Right tangent at x=${x0.toFixed(2)}`,
          line: {
            color: darkerColor,
            width: 2.5,
            dash: 'dot',
          },
        });
      } else {
        // Draw single tangent line
        const slope = isFinite(slopeLeft) ? slopeLeft : slopeRight;

        if (!isFinite(slope)) {
          return;
        }

        const x_tangent = [x0 - extend, x0 + extend];
        const y_tangent = x_tangent.map(x => y0 + slope * (x - x0));

        traces.push({
          x: x_tangent,
          y: y_tangent,
          type: 'scatter',
          mode: 'lines',
          name: `Tangent at x=${x0.toFixed(2)}`,
          line: {
            color: baseColor,
            width: 2.5,
            dash: 'dot',
          },
        });
      }

      // Add point at tangent location
      traces.push({
        x: [x0],
        y: [y0],
        type: 'scatter',
        mode: 'markers',
        name: `Point at x=${x0.toFixed(2)}`,
        marker: {
          color: baseColor,
          size: 10,
          line: { color: 'black', width: 2 },
        },
        showlegend: false,
      });
    });

    const isSmallScreen = SCREEN_WIDTH <= 768;

    const layout = {
      title: {
        text: `f(x) = ${funcInput}`,
        font: {
          family: 'Courier',
          size: 18,
          color: isDark ? '#e4e8f0' : '#0f172a',
        },
      },
      xaxis: {
        title: 'x',
        range: [xMinNum, xMaxNum],
        gridcolor: isDark ? '#374151' : '#e2e8f0',
        zerolinecolor: isDark ? '#6366f1' : '#4f46e5',
        color: isDark ? '#e4e8f0' : '#0f172a',
      },
      yaxis: {
        title: 'y',
        range: [yMinNum, yMaxNum],
        gridcolor: isDark ? '#374151' : '#e2e8f0',
        zerolinecolor: isDark ? '#6366f1' : '#4f46e5',
        color: isDark ? '#e4e8f0' : '#0f172a',
      },
      plot_bgcolor: isDark ? '#1a1f3a' : '#ffffff',
      paper_bgcolor: isDark ? '#1a1f3a' : '#ffffff',
      font: { color: isDark ? '#e4e8f0' : '#0f172a' },
      showlegend: showLegend,
      legend: {
        bgcolor: isDark ? 'rgba(26, 31, 58, 0.8)' : 'rgba(255, 255, 255, 0.8)',
        bordercolor: isDark ? '#6366f1' : '#4f46e5',
        borderwidth: 1,
        orientation: isSmallScreen ? 'h' : 'v',
        x: isSmallScreen ? 0.5 : 1.02,
        y: isSmallScreen ? 1.25 : 1,
        xanchor: isSmallScreen ? 'center' : 'left',
        yanchor: isSmallScreen ? 'top' : 'top',
      },
      margin: {
        t: isSmallScreen ? 150 : 80,
        b: 60,
        l: 60,
        r: isSmallScreen ? 20 : 200,
      },
    };

    const config = {
      displayModeBar: true,
      displaylogo: false,
      responsive: true,
    };

    return (
      <View 
        ref={graphRef}
        style={[styles.graphContainer, { backgroundColor: colors.glassBg, borderColor: colors.glassBorder }]}
        collapsable={false}
      >
        <Plotly
          data={traces}
          layout={layout}
          config={config}
          style={styles.plotlyGraph}
        />
      </View>
    );
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.bgPrimary }]}>
      <StatusBar barStyle={isDark ? 'light-content' : 'dark-content'} />
      
      {/* Toast notifications */}
      <Toast message={toast.message} type={toast.type} visible={toast.visible} onHide={hideToast} />
      
      {/* Header with theme and legend toggles */}
      <View style={styles.header}>
        <View style={styles.headerContent}>
          <Text style={[styles.title, { color: colors.accentPrimary }]}>∫ Function Grapher</Text>
          <Text style={[styles.subtitle, { color: colors.textSecondary }]}>
            Real-time mathematical visualization & analysis
          </Text>
        </View>
        <View style={styles.headerButtons}>
          <TouchableOpacity
            style={[styles.headerButton, { backgroundColor: colors.glassBg, borderColor: colors.glassBorder }]}
            onPress={handleDownloadPlot}
          >
            <Text style={{ fontSize: 16 }}>💾</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.headerButton, { backgroundColor: colors.glassBg, borderColor: colors.glassBorder }]}
            onPress={handleSharePlot}
          >
            <Text style={{ fontSize: 16 }}>📤</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.headerButton, { backgroundColor: colors.glassBg, borderColor: colors.glassBorder }]}
            onPress={() => setShowLegend(!showLegend)}
          >
            <Text style={{ fontSize: 16 }}>📊</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.headerButton, { backgroundColor: colors.glassBg, borderColor: colors.glassBorder }]}
            onPress={toggleTheme}
          >
            <Text style={{ fontSize: 16 }}>{isDark ? '🌙' : '☀️'}</Text>
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Input Section */}
        <View style={[styles.section, { backgroundColor: colors.glassBg, borderColor: colors.glassBorder }]}>
          <Text style={[styles.label, { color: colors.textSecondary }]}>FUNCTION f(x)</Text>
          <TextInput
            style={[styles.input, { backgroundColor: colors.bgSecondary, borderColor: colors.borderColor, color: colors.textPrimary }]}
            value={funcInput}
            onChangeText={setFuncInput}
            placeholder="e.g., x^2, sin(x), (x²-1)/(x-1)"
            placeholderTextColor={colors.textSecondary}
          />

          <View style={styles.rangeGrid}>
            <View style={styles.rangeItem}>
              <Text style={[styles.label, { color: colors.textSecondary }]}>X MIN</Text>
              <TextInput
                style={[styles.inputSmall, { backgroundColor: colors.bgSecondary, borderColor: colors.borderColor, color: colors.textPrimary }]}
                value={xMin}
                onChangeText={setXMin}
                keyboardType="numeric"
                placeholderTextColor={colors.textSecondary}
              />
            </View>
            <View style={styles.rangeItem}>
              <Text style={[styles.label, { color: colors.textSecondary }]}>X MAX</Text>
              <TextInput
                style={[styles.inputSmall, { backgroundColor: colors.bgSecondary, borderColor: colors.borderColor, color: colors.textPrimary }]}
                value={xMax}
                onChangeText={setXMax}
                keyboardType="numeric"
                placeholderTextColor={colors.textSecondary}
              />
            </View>
            <View style={styles.rangeItem}>
              <Text style={[styles.label, { color: colors.textSecondary }]}>Y MIN</Text>
              <TextInput
                style={[styles.inputSmall, { backgroundColor: colors.bgSecondary, borderColor: colors.borderColor, color: colors.textPrimary }]}
                value={yMin}
                onChangeText={setYMin}
                keyboardType="numeric"
                placeholderTextColor={colors.textSecondary}
              />
            </View>
            <View style={styles.rangeItem}>
              <Text style={[styles.label, { color: colors.textSecondary }]}>Y MAX</Text>
              <TextInput
                style={[styles.inputSmall, { backgroundColor: colors.bgSecondary, borderColor: colors.borderColor, color: colors.textPrimary }]}
                value={yMax}
                onChangeText={setYMax}
                keyboardType="numeric"
                placeholderTextColor={colors.textSecondary}
              />
            </View>
          </View>

          {/* Display Options */}
          <View style={styles.controlsGrid}>
            <CheckboxItem label="Function f(x)" checked={showFunction} onToggle={setShowFunction} colors={colors} color="#1f77b4" />
            <CheckboxItem label="Derivative f'(x)" checked={showDerivative} onToggle={setShowDerivative} colors={colors} color="#ff7f0e" />
            <CheckboxItem label="2nd Derivative" checked={showSecondDerivative} onToggle={setShowSecondDerivative} colors={colors} color="#2ca02c" />
            <CheckboxItem label="Critical Points" checked={showCritical} onToggle={setShowCritical} colors={colors} color="#d62728" />
            <CheckboxItem label="Roots" checked={showRoots} onToggle={setShowRoots} colors={colors} color="#9467bd" />
            <CheckboxItem label="Inflection" checked={showInflection} onToggle={setShowInflection} colors={colors} color="#8c564b" />
            <CheckboxItem label="Undefined" checked={showUndefined} onToggle={setShowUndefined} colors={colors} color="#ff0000" />
            <CheckboxItem label="Vert. Asymptotes" checked={showVerticalAsymptotes} onToggle={setShowVerticalAsymptotes} colors={colors} color="#e377c2" />
            <CheckboxItem label="Horiz. Asymptote" checked={showHorizontalAsymptote} onToggle={setShowHorizontalAsymptote} colors={colors} color="#7f7f7f" />
            <CheckboxItem label="Oblique Asymptote" checked={showObliqueAsymptote} onToggle={setShowObliqueAsymptote} colors={colors} color="#17becf" />
          </View>

          {/* Tangent Lines */}
          <View style={styles.tangentSection}>
            <Text style={[styles.label, { color: colors.textSecondary }]}>ADD TANGENT LINE</Text>
            <View style={styles.tangentControls}>
              <TextInput
                style={[styles.inputSmall, { flex: 1, backgroundColor: colors.bgSecondary, borderColor: colors.borderColor, color: colors.textPrimary }]}
                value={tangentInput}
                onChangeText={setTangentInput}
                placeholder="x-coordinate"
                keyboardType="numeric"
                placeholderTextColor={colors.textSecondary}
              />
              <TouchableOpacity
                style={[styles.button, { backgroundColor: colors.accentPrimary }]}
                onPress={addTangent}
              >
                <Text style={styles.buttonText}>Add</Text>
              </TouchableOpacity>
            </View>
            <View style={styles.tangentList}>
              {tangentLines.map((x, idx) => (
                <View key={idx} style={[styles.tangentTag, { backgroundColor: colors.bgTertiary, borderColor: colors.borderColor }]}>
                  <Text style={[styles.tangentTagText, { color: colors.textPrimary }]}>
                    x = {x.toFixed(2)}
                  </Text>
                  <TouchableOpacity onPress={() => removeTangent(x)}>
                    <Text style={styles.removeButton}>×</Text>
                  </TouchableOpacity>
                </View>
              ))}
            </View>
          </View>
        </View>

        {/* Graph */}
        {renderGraph()}

        {/* Analysis */}
        {analysis && (
          <View style={[styles.section, { backgroundColor: colors.glassBg, borderColor: colors.glassBorder }]}>
            <Text style={[styles.sectionTitle, { color: colors.textPrimary }]}>Mathematical Analysis</Text>
            
            <AnalysisCard
              title="Function Expressions"
              content={`f(x) = ${funcInput}\nf'(x) = ${analyzer?.derivNode.toString()}\nf''(x) = ${analyzer?.secondDerivNode.toString()}`}
              colors={colors}
            />

            <AnalysisCard
              title={`Critical Points (${analysis.criticalPoints.length})`}
              content={analysis.criticalPoints.length > 0
                ? analysis.criticalPoints.map(p => `(${p.x.toFixed(4)}, ${p.y.toFixed(4)})`).join('\n')
                : 'None found'}
              colors={colors}
            />

            <AnalysisCard
              title={`Roots/Zeros (${analysis.roots.length})`}
              content={analysis.roots.length > 0
                ? analysis.roots.map(r => `x = ${r.toFixed(4)}`).join('\n')
                : 'None found'}
              colors={colors}
            />

            <AnalysisCard
              title={`Inflection Points (${analysis.inflectionPoints.length})`}
              content={analysis.inflectionPoints.length > 0
                ? analysis.inflectionPoints.map(p => `(${p.x.toFixed(4)}, ${p.y.toFixed(4)})`).join('\n')
                : 'None found'}
              colors={colors}
            />

            <AnalysisCard
              title={`Undefined Values (Holes) (${analysis.undefinedValues.length})`}
              content={analysis.undefinedValues.length > 0
                ? analysis.undefinedValues.map(p => `x = ${p.x.toFixed(4)}, limit = ${p.y.toFixed(4)}`).join('\n')
                : 'None found'}
              colors={colors}
            />

            <AnalysisCard
              title="Asymptotes"
              content={[
                analysis.verticalAsymptotes.length > 0 ? `Vertical:\n${analysis.verticalAsymptotes.map(a => `x = ${a.toFixed(4)}`).join('\n')}` : '',
                analysis.horizontalAsymptote !== null ? `Horizontal:\ny = ${analysis.horizontalAsymptote.toFixed(4)}` : '',
                analysis.obliqueAsymptote !== null ? `Oblique:\ny = ${analysis.obliqueAsymptote.m.toFixed(4)}x + ${analysis.obliqueAsymptote.b.toFixed(4)}` : ''
              ].filter(Boolean).join('\n\n') || 'None found'}
              colors={colors}
            />

            <AnalysisCard
              title="Domain"
              content={`All real numbers ℝ\n(computed over [${xMin}, ${xMax}])`}
              colors={colors}
            />
          </View>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingTop: Platform.OS === 'ios' ? 50 : StatusBar.currentHeight || 0,
  },
  scrollView: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 20,
  },
  headerContent: {
    flex: 1,
  },
  headerButtons: {
    flexDirection: 'row',
    gap: 10,
  },
  headerButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    borderWidth: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    marginBottom: 4,
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
  },
  subtitle: {
    fontSize: 12,
    fontWeight: '400',
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
  },
  section: {
    marginHorizontal: 20,
    marginBottom: 20,
    padding: 20,
    borderRadius: 20,
    borderWidth: 1,
  },
  label: {
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 8,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
  },
  input: {
    width: '100%',
    padding: 16,
    borderRadius: 12,
    borderWidth: 2,
    fontSize: 16,
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
    marginBottom: 16,
  },
  inputSmall: {
    padding: 12,
    borderRadius: 12,
    borderWidth: 2,
    fontSize: 14,
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
  },
  rangeGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 16,
  },
  rangeItem: {
    flex: 1,
    minWidth: 150,
  },
  controlsGrid: {
    marginTop: 16,
    gap: 8,
  },
  controlItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 12,
    borderWidth: 2,
    gap: 12,
  },
  checkbox: {
    width: 20,
    height: 20,
    borderRadius: 6,
    borderWidth: 2,
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkmark: {
    color: 'white',
    fontSize: 14,
    fontWeight: 'bold',
  },
  controlLabel: {
    flex: 1,
    fontSize: 14,
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
  },
  colorIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  tangentSection: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
  },
  tangentControls: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 12,
  },
  button: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  buttonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
    textTransform: 'uppercase',
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
  },
  tangentList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  tangentTag: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 8,
    borderRadius: 20,
    borderWidth: 1,
    gap: 8,
  },
  tangentTagText: {
    fontSize: 12,
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
  },
  removeButton: {
    fontSize: 20,
    color: '#ef4444',
  },
  graphContainer: {
    marginHorizontal: 20,
    marginBottom: 20,
    padding: 20,
    borderRadius: 20,
    borderWidth: 1,
    position: 'relative',
    height: GRAPH_HEIGHT + 80, // Account for padding
  },
  plotlyGraph: {
    flex: 1,
    width: '100%',
  },
  errorText: {
    fontSize: 14,
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
    textAlign: 'center',
    padding: 20,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 16,
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
  },
  analysisCard: {
    backgroundColor: '#1a1f3a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderLeftWidth: 4,
  },
  analysisCardTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
    textTransform: 'uppercase',
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
  },
  analysisCardContent: {
    fontSize: 13,
    lineHeight: 20,
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
  },
  toast: {
    position: 'absolute',
    top: Platform.OS === 'ios' ? 60 : (StatusBar.currentHeight || 0) + 10,
    left: 20,
    right: 20,
    padding: 16,
    borderRadius: 12,
    zIndex: 1000,
    elevation: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  toastText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
    textAlign: 'center',
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
  },
});