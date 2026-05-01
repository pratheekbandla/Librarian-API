import PDFUpload from "@/components/PDFUpload";
import ChatInterface from "@/components/ChatInterface";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center p-4 md:p-8">
      <div className="w-full max-w-7xl h-[calc(100vh-4rem)] md:h-[calc(100vh-6rem)] flex flex-col md:flex-row gap-6">
        
        {/* Left Panel */}
        <div className="w-full md:w-1/3 flex flex-col gap-6">
          <div>
            <h1 className="text-3xl font-bold mb-2">Librarian AI 📚</h1>
            <p className="text-neutral-400">Chat with your documents</p>
          </div>
          
          <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6 flex-1 flex flex-col">
            <h2 className="text-lg font-semibold mb-4 text-neutral-200">Library Ingestion</h2>
            <div className="flex-1 flex flex-col justify-center">
              <PDFUpload />
            </div>
          </div>
        </div>

        {/* Separator on desktop */}
        <div className="hidden md:block w-px bg-neutral-800 mx-2"></div>

        {/* Right Panel */}
        <div className="w-full md:w-2/3 h-[50vh] md:h-full">
          <ChatInterface />
        </div>

      </div>
    </main>
  );
}
