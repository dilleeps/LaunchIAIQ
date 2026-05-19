import { PageHeader } from "../components/PageHeader";

export function Stub({ title, message }: { title: string; message: string }) {
  return (
    <>
      <PageHeader eyebrow="Phase 2" title={title} subtitle={message} />
      <div className="px-10 py-12 text-mute font-mono text-sm">
        Coming in a follow-up PR. The data model already supports this view — only the rendering layer is deferred.
      </div>
    </>
  );
}
