import IaPageIntro from '../components/IaPageIntro.jsx'
import IaSidebar from '../components/IaSidebar.jsx'
import IaTopbar from '../components/IaTopbar.jsx'
import TranscriptionForm from '../components/TranscriptionForm.jsx'
import './IaPage.css'

export default function IaPage({ usuario, logout }) {
  return (
    <main className="ia-page">
      <IaSidebar onLogout={logout} />
      <div className="ia-main">
        <IaTopbar usuario={usuario} />
        <section className="ia-content">
          <IaPageIntro />
          <TranscriptionForm />
        </section>
      </div>
    </main>
  )
}
