"use client";

import CodeMirror from "@uiw/react-codemirror";
import { sql } from "@codemirror/lang-sql";
import { oneDark } from "@codemirror/theme-one-dark";
import { EditorView } from "@codemirror/view";

const editorTheme = EditorView.theme({
  "&": { backgroundColor: "transparent" },
  ".cm-gutters": { backgroundColor: "transparent", border: "none" },
  ".cm-activeLineGutter": { backgroundColor: "transparent" },
  ".cm-activeLine": { backgroundColor: "rgba(255,255,255,0.03)" },
});

interface SqlEditorProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export default function SqlEditor({ value, onChange, disabled }: SqlEditorProps) {
  return (
    <CodeMirror
      value={value}
      onChange={onChange}
      extensions={[sql(), editorTheme]}
      theme={oneDark}
      minHeight="180px"
      maxHeight="400px"
      editable={!disabled}
      basicSetup={{
        lineNumbers: true,
        foldGutter: false,
        dropCursor: false,
        highlightActiveLine: true,
        highlightSelectionMatches: false,
      }}
      className="overflow-hidden rounded-lg border border-slate-700"
    />
  );
}
