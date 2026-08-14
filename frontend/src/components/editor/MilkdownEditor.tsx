import React, { useRef } from 'react';
import { defaultValueCtx, Editor, rootCtx, editorViewOptionsCtx } from '@milkdown/core';
import { Milkdown, MilkdownProvider, useEditor } from '@milkdown/react';
import { commonmark } from '@milkdown/preset-commonmark';
import { gfm } from '@milkdown/preset-gfm';
import { listener, listenerCtx } from '@milkdown/plugin-listener';
import { history } from '@milkdown/plugin-history';
import { clipboard } from '@milkdown/plugin-clipboard';
import { prism, prismConfig } from '@milkdown/plugin-prism';
import { refractor } from 'refractor/all';

interface MilkdownEditorProps {
  noteId: string;
  initialContent: string;
  readOnly?: boolean;
  onChange: (markdown: string) => void;
}

const EditorInner: React.FC<MilkdownEditorProps> = ({
  initialContent,
  readOnly = false,
  onChange,
}) => {
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  const { get } = useEditor((root) =>
    Editor.make()
      .config((ctx) => {
        ctx.set(rootCtx, root);
        ctx.set(defaultValueCtx, initialContent || '');
        if (readOnly) {
          ctx.set(editorViewOptionsCtx, { editable: () => false });
        }
        ctx.set(prismConfig.key, {
          configureRefractor: () => refractor,
        });
        const listenerPlugin = ctx.get(listenerCtx);
        listenerPlugin.markdownUpdated((_, markdown) => {
          if (!readOnly) {
            onChangeRef.current(markdown);
          }
        });
      })
      .use(commonmark)
      .use(gfm)
      .use(prism)
      .use(history)
      .use(clipboard)
      .use(listener)
  );

  return (
    <div className="milkdown-wrapper w-full h-full min-h-[400px]">
      <Milkdown />
    </div>
  );
};

export const MilkdownEditor: React.FC<MilkdownEditorProps> = ({
  noteId,
  initialContent,
  readOnly = false,
  onChange,
}) => {
  return (
    <MilkdownProvider key={noteId}>
      <EditorInner
        noteId={noteId}
        initialContent={initialContent}
        readOnly={readOnly}
        onChange={onChange}
      />
    </MilkdownProvider>
  );
};
