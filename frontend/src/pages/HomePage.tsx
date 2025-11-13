import TrafficDashboard from "@/modules/features/traffic/components/TrafficDashboard";

export default function HomePage() {
  return (
    <div className="relative min-h-screen">
      <TrafficDashboard />

      {/* Floating QR bottom-right */}
      <a
        href="https://t.me/fireappdetectbot"
        target="_blank"
        rel="noreferrer"
        className="fixed bottom-4 right-4 z-50 group"
        title="Mở Telegram: @fireappdetectbot"
      >
        <div className="rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 bg-white/95 dark:bg-gray-900/90 backdrop-blur supports-[backdrop-filter]:bg-white/80 dark:supports-[backdrop-filter]:bg-gray-900/70 p-2 transition-transform group-hover:scale-[1.02]">
          <img
            src="/images/fireappdetectbot-qr.png"
            alt="QR Telegram @fireappdetectbot"
            className="w-36 h-36 object-contain"
            loading="lazy"
          />
          <div className="mt-1 text-center text-xs font-medium text-gray-700 dark:text-gray-300">
            QR: @fireappdetectbot
          </div>
        </div>
      </a>
    </div>
  );
}
