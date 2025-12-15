export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm">
        <h1 className="text-4xl font-bold mb-8 text-center">
          Procurement AI MVP
        </h1>
        <p className="text-center text-muted-foreground mb-8">
          AI-powered procurement request management system
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-center">
          <div className="p-6 border rounded-lg">
            <h2 className="text-xl font-semibold mb-2">For Requestors</h2>
            <p className="text-muted-foreground">
              Create and track procurement requests with AI-powered document extraction
            </p>
          </div>
          <div className="p-6 border rounded-lg">
            <h2 className="text-xl font-semibold mb-2">For Procurement Team</h2>
            <p className="text-muted-foreground">
              Manage and process requests with automated commodity classification
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
