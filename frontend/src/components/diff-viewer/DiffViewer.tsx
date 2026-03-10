import { DiffEditor } from '@monaco-editor/react';

interface Props {
  original: string;
  modified: string;
}

export default function DiffViewer({ original, modified }: Props) {
  return (
    <DiffEditor
      height="100%"
      language="plaintext"
      original={original}
      modified={modified}
      theme="vs-dark"
      options={{
        readOnly: true,
        renderSideBySide: true,
        minimap: { enabled: false },
        fontSize: 13,
      }}
    />
  );
}
