import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Pill, ArrowLeft } from "lucide-react"
import Link from "next/link"

export default function DisclaimerPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <Pill className="h-6 w-6" />
            </div>
            <span className="font-montserrat font-black text-xl">MediBot</span>
          </Link>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="mb-6">
          <Button variant="outline" asChild>
            <Link href="/">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Home
            </Link>
          </Button>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-2xl font-montserrat font-black">Medical Disclaimer</CardTitle>
          </CardHeader>
          <CardContent className="prose prose-sm max-w-none space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-3">Important Notice</h3>
              <p className="text-muted-foreground leading-relaxed">
                The information provided by MediBot is for educational and informational purposes only. It is not
                intended as a substitute for professional medical advice, diagnosis, or treatment.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-semibold mb-3">Medical Advice Disclaimer</h3>
              <ul className="space-y-2 text-muted-foreground">
                <li>
                  • Always seek the advice of your physician or other qualified health provider with any questions you
                  may have regarding a medical condition.
                </li>
                <li>
                  • Never disregard professional medical advice or delay in seeking it because of something you have
                  read on this platform.
                </li>
                <li>
                  • If you think you may have a medical emergency, call your doctor or emergency services immediately.
                </li>
              </ul>
            </div>

            <div>
              <h3 className="text-lg font-semibold mb-3">Information Accuracy</h3>
              <p className="text-muted-foreground leading-relaxed">
                While we strive to provide accurate and up-to-date information, we make no representations or warranties
                of any kind, express or implied, about the completeness, accuracy, reliability, suitability, or
                availability of the information contained on this platform.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-semibold mb-3">AI-Generated Content</h3>
              <p className="text-muted-foreground leading-relaxed">
                Our AI advice feature provides general information based on available medical literature. This content
                should not be considered as personalized medical advice and may not be applicable to your specific
                health condition.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-semibold mb-3">Drug Information Sources</h3>
              <p className="text-muted-foreground leading-relaxed">
                Drug information is compiled from various sources including official databases, manufacturer
                information, and regulatory authorities. Prices and availability may vary and should be verified with
                local pharmacies.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-semibold mb-3">Limitation of Liability</h3>
              <p className="text-muted-foreground leading-relaxed">
                MediBot and its operators shall not be liable for any direct, indirect, incidental, consequential, or
                punitive damages arising out of your use of this platform or the information provided herein.
              </p>
            </div>

            <div className="bg-primary/5 p-4 rounded-lg border border-primary/20">
              <p className="text-sm font-medium text-primary">
                By using MediBot, you acknowledge that you have read, understood, and agree to be bound by this
                disclaimer.
              </p>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
