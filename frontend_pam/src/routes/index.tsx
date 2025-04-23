import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/')({
  component: Index,
})

function Index() {
  return (
    <div className="flex flex-col h-screen p-5">
     
      <h1 className="text-2xl md:text-3xl font-bold leading-relaxed">
        Towards a Transnational Acoustic Biodiversity Monitoring Network (TABMON)
      </h1>

      
      <div className="flex flex-col md:flex-row mt-3">
        
        
        <div className="w-full md:w-1/2 p-5">
          <p className="mt-4 leading-relaxed text-base sm:text-lg">
            The central objective of TABMON is to develop a transnational
            biodiversity monitoring with autonomous acoustic sensors across a 
            large latitudinal range in Europe, demonstrating how acoustic sensing
            can complement existing monitoring efforts to fill current gaps in
            reporting to EU directives and assessing targets of the EU
            Biodiversity Strategy target.
          </p>

          <p className="mt-4 text-base sm:text-lg">
            More info can be found on{' '}
            <a
              href="https://www.nina.no/english/TABMON"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 underline hover:text-blue-800"
            >
              NINA's official TABMON page
            </a>.
          </p>

          <img className="mt-4 w-full" src="../public/tabmon_1.jpg" alt="Tabmon" />
        </div>

        
        <div className="w-full md:w-1/2 p-5">
          <p className="mt-4 leading-relaxed text-base sm:text-lg">
            TABMON is divided in three work packages.
          </p>
          <ol className="mt-4 list-decimal list-inside leading-relaxed text-base sm:text-lg font-bold">
            <li>Deploying the transnational monitoring network</li>
            <li>Using AI tools to derive Essential Biodiversity Variables (EBV) from the acoustic dataset to estimate ecosystems and species population health</li>
            <li>Showcase our results to help inform policy makers</li>
          </ol>

          <img className="mt-4 w-full" src="../public/tabmon_packages.png" alt="Tabmon packages" />
          <p className="mt-2 text-gray-700 text-sm italic">
            Illustration of the three work packages in the TABMON project.
          </p>
        </div>

      </div>
    </div>
  )
}
