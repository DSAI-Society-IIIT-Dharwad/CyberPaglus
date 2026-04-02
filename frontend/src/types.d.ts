declare module 'html2pdf.js' {
  interface Html2PdfOptions {
    margin?: number | number[];
    filename?: string;
    image?: { type?: string; quality?: number };
    html2canvas?: { scale?: number; backgroundColor?: string };
    jsPDF?: { unit?: string; format?: string; orientation?: string };
  }

  interface Html2PdfInstance {
    set(options: Html2PdfOptions): Html2PdfInstance;
    from(element: HTMLElement): Html2PdfInstance;
    save(): Promise<void>;
  }

  function html2pdf(): Html2PdfInstance;
  export default html2pdf;
}

declare module 'react-force-graph-2d' {
  import { Component, RefObject } from 'react';
  
  export interface ForceGraphMethods {
    d3Force(forceName: string, force?: any): any;
    centerAt(x?: number, y?: number, ms?: number): void;
    zoom(amount: number, ms?: number): void;
    zoomToFit(ms?: number, padding?: number): void;
    screen2GraphCoords(x: number, y: number): { x: number; y: number };
    graph2ScreenCoords(x: number, y: number): { x: number; y: number };
  }
  
  const ForceGraph2D: React.ForwardRefExoticComponent<any & React.RefAttributes<ForceGraphMethods>>;
  export default ForceGraph2D;
  export type { ForceGraphMethods };
}
