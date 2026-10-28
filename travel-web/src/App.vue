<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { fetchRecommendations, fetchUsers, type TravelPackage, type User } from './api'

const users = ref<User[]>([])
const selectedUserId = ref('')
const selectedUser = computed(() => users.value.find((user) => user.id === selectedUserId.value))
const packages = ref<TravelPackage[]>([])
const loadingUsers = ref(true)
const loadingPackages = ref(false)
const usersError = ref(false)
const packagesError = ref(false)
let request: AbortController | undefined

const currency = new Intl.NumberFormat('es-CO', {
  style: 'currency', currency: 'USD', currencyDisplay: 'code', maximumFractionDigits: 2,
})
const money = (value: string) => currency.format(Number(value))
const date = (value: string) => new Intl.DateTimeFormat('es-CO', {
  day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC',
}).format(new Date(`${value}T12:00:00Z`))
const flightTime = (value: string) => new Intl.DateTimeFormat('es-CO', {
  hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'America/Bogota',
}).format(new Date(value))
const flightDate = (value: string) => new Intl.DateTimeFormat('es-CO', {
  day: 'numeric', month: 'short', timeZone: 'America/Bogota',
}).format(new Date(value))

async function loadUsers() {
  loadingUsers.value = true
  usersError.value = false
  try {
    users.value = (await fetchUsers()).users
    selectedUserId.value = users.value[0]?.id ?? ''
  } catch {
    usersError.value = true
  } finally {
    loadingUsers.value = false
  }
}

async function loadPackages() {
  request?.abort()
  const controller = new AbortController()
  request = controller
  packages.value = []
  packagesError.value = false
  if (!selectedUserId.value) return
  loadingPackages.value = true
  try {
    const result = await fetchRecommendations(selectedUserId.value, controller.signal)
    if (!controller.signal.aborted) packages.value = result.recommendations
  } catch {
    if (!controller.signal.aborted) packagesError.value = true
  } finally {
    if (!controller.signal.aborted) loadingPackages.value = false
  }
}

watch(selectedUserId, loadPackages)
onMounted(loadUsers)
onBeforeUnmount(() => request?.abort())
</script>

<template>
  <div class="app-shell">
    <header class="site-header">
      <div class="header-content">
        <a class="brand" href="/" aria-label="Aterrizar demo, inicio">
          aterrizar<span class="demo-badge">DEMO</span>
        </a>
        <div class="user-picker">
          <span class="avatar" aria-hidden="true">{{ selectedUser?.name[0] ?? '·' }}</span>
          <div>
            <label for="user-select">Estás explorando como</label>
            <select id="user-select" v-model="selectedUserId" :disabled="loadingUsers || !users.length">
              <option v-if="!users.length" value="">{{ loadingUsers ? 'Cargando usuarios…' : 'Sin usuarios' }}</option>
              <option v-for="user in users" :key="user.id" :value="user.id">{{ user.name }} · {{ user.profile }}</option>
            </select>
          </div>
        </div>
      </div>
    </header>

    <main>
      <section class="hero">
        <div class="hero-content">
          <p class="eyebrow"><span aria-hidden="true">✧</span> VIAJES QUE VAN CONTIGO</p>
          <h1>Tu próximo viaje,<br /><span>a tu manera.</span></h1>
          <p>Un alojamiento y tus vuelos de ida y vuelta.<br class="desktop-break" /> Todo junto, pensado para ti.</p>
          <div class="hero-stamp" aria-hidden="true">
            <svg viewBox="0 0 220 160" fill="none">
              <path d="M16 134C140 147 25 24 129 53S196 29 208 16" stroke="currentColor" stroke-width="2" stroke-dasharray="5 7" />
              <path d="m128 26 11 29 29 11-7 7-27-4-15 15 1 10-6 6-7-17-17-7 6-6 10 1 15-15-4-27z" fill="currentColor" />
            </svg>
            <span>EL VIAJE EMPIEZA AQUÍ</span>
          </div>
        </div>
      </section>

      <div class="main-content">
        <div v-if="loadingUsers" class="state-card" role="status">Cargando los perfiles de viajeros…</div>
        <div v-else-if="usersError" class="state-card error-state" role="alert">
          <h2>No pudimos cargar los usuarios</h2>
          <p>Comprueba que la API esté disponible e inténtalo de nuevo.</p>
          <button @click="loadUsers">Reintentar</button>
        </div>
        <div v-else-if="!users.length" class="state-card">
          <h2>Aún no hay viajeros</h2>
          <p>Cuando haya perfiles disponibles, podrás elegir uno y ver sus recomendaciones.</p>
        </div>

        <template v-else-if="selectedUser">
          <section class="profile-summary" aria-label="Preferencias del viajero">
            <div class="profile-copy">
              <span class="profile-icon" aria-hidden="true">✧</span>
              <div><strong>{{ selectedUser.profile }}</strong><p>{{ selectedUser.description }}</p></div>
            </div>
            <div class="profile-facts">
              <div><span>Salida desde</span><strong>{{ selectedUser.origin === 'MDE' ? 'Medellín · MDE' : selectedUser.origin }}</strong></div>
              <div><span>Viajeros</span><strong>{{ selectedUser.party_size }} personas</strong></div>
              <div><span>Presupuesto / persona</span><strong>{{ money(selectedUser.max_price_per_person_usd) }}</strong></div>
            </div>
          </section>

          <section class="results" aria-labelledby="results-title" :aria-busy="loadingPackages">
            <div class="results-heading">
              <div><p class="section-kicker">TU SELECCIÓN PERSONALIZADA</p><h2 id="results-title">Paquetes para {{ selectedUser.name }}</h2></div>
              <span v-if="!loadingPackages && !packagesError" class="results-count">{{ packages.length }} {{ packages.length === 1 ? 'opción' : 'opciones' }}</span>
            </div>
            <div aria-live="polite">
              <p v-if="loadingPackages" class="loading-label" role="status">Buscando paquetes para {{ selectedUser.name }}…</p>
              <template v-if="loadingPackages">
                <div v-for="n in 2" :key="n" class="skeleton" aria-hidden="true"><span></span><div><i></i><i></i><i></i></div></div>
              </template>
              <div v-else-if="packagesError" class="state-card error-state" role="alert">
                <h3>No pudimos cargar los paquetes</h3>
                <p>Vuelve a intentarlo para ver las recomendaciones de {{ selectedUser.name }}.</p>
                <button @click="loadPackages">Reintentar</button>
              </div>
              <div v-else-if="!packages.length" class="state-card">
                <span class="empty-icon" aria-hidden="true">⌁</span>
                <h3>El viaje ideal aún está por llegar</h3>
                <p>No hay combinaciones disponibles que cumplan con el presupuesto y el número de viajeros de este perfil.</p>
                <p>Puedes explorar las recomendaciones de otro usuario.</p>
              </div>
            </div>

            <article v-for="(item, index) in packages" :key="item.id" class="package-card">
              <div class="destination-art" :class="{ nature: ['BGA', 'PEI'].includes(item.accommodation.airport), city: item.accommodation.airport === 'BOG' }" aria-hidden="true">
                <span class="trip-label">VUELO + ALOJAMIENTO</span>
                <div class="landscape"><span class="sun"></span><span class="hill hill-back"></span><span class="hill hill-front"></span></div>
                <div class="destination-code"><span>{{ item.accommodation.airport }}</span><small>{{ item.nights }} noches para desconectar</small></div>
              </div>
              <div class="package-body">
                <div class="package-topline"><span class="recommendation-label">{{ index === 0 ? 'Tu mejor coincidencia' : 'También te puede gustar' }}</span><span class="match">{{ Math.round(item.score * 100) }}% de afinidad</span></div>
                <h3>{{ item.name }}</h3>
                <p class="destination">{{ item.destination }}</p>
                <div class="stay-info"><span class="component-icon" aria-hidden="true">▥</span><div><strong>{{ item.accommodation.hotel }}</strong><p>{{ date(item.accommodation.check_in) }} – {{ date(item.accommodation.check_out) }} · {{ item.nights }} noches</p></div></div>
                <div class="flight-list" aria-label="Vuelos incluidos">
                  <div v-for="leg in [{ label: 'Ida', flight: item.outbound_flight }, { label: 'Vuelta', flight: item.return_flight }]" :key="leg.label" class="flight-row">
                    <span class="component-icon" aria-hidden="true">{{ leg.label === 'Ida' ? '↗' : '↙' }}</span>
                    <span class="flight-direction">{{ leg.label }}</span>
                    <strong>{{ leg.flight.origin }} <span class="route-arrow">→</span> {{ leg.flight.destination }}</strong>
                    <span class="flight-schedule">{{ flightDate(leg.flight.departure_at) }} · {{ flightTime(leg.flight.departure_at) }}–{{ flightTime(leg.flight.arrival_at) }}</span>
                  </div>
                </div>
              </div>
              <div class="package-price">
                <span class="included-badge">Ida + vuelta + hotel</span>
                <span class="price-label">Precio por persona</span>
                <strong>{{ money(item.price_per_person_usd) }}</strong>
                <p>{{ money(item.total_price_usd) }} en total<br />para {{ selectedUser.party_size }} personas</p>
                <span class="budget-note">Dentro de tu presupuesto</span>
              </div>
              <details class="package-detail">
                <summary>Ver detalle del paquete <span aria-hidden="true">＋</span></summary>
                <div class="detail-content">
                  <div><h4>Tu estancia</h4><p>{{ item.description }}</p><p>Aeropuerto de llegada: {{ item.accommodation.airport }}. Los traslados terrestres no están incluidos.</p></div>
                  <div><h4>Tus vuelos</h4><p v-for="flight in [item.outbound_flight, item.return_flight]" :key="flight.id">{{ flight.airline }} · {{ flight.flight_number }}<br />{{ flight.cabin }} · {{ flight.origin }} → {{ flight.destination }}</p><small>Horarios de Colombia (UTC−5).</small></div>
                  <div><h4>Desglose por persona</h4><dl><div><dt>Alojamiento · {{ item.nights }} noches</dt><dd>{{ money(item.accommodation.price_per_person_usd) }}</dd></div><div><dt>Vuelo de ida</dt><dd>{{ money(item.outbound_flight.price_per_person_usd) }}</dd></div><div><dt>Vuelo de vuelta</dt><dd>{{ money(item.return_flight.price_per_person_usd) }}</dd></div><div class="breakdown-total"><dt>Total</dt><dd>{{ money(item.price_per_person_usd) }}</dd></div></dl></div>
                </div>
              </details>
            </article>
            <p v-if="packages.length" class="selection-note"><span aria-hidden="true">✧</span> Elegidos según tus intereses, presupuesto y número de viajeros.</p>
          </section>
        </template>
        <footer><span class="footer-brand">aterrizar <span>demo</span></span><p>Perfiles, alojamientos, vuelos y precios ficticios. Esta demo no realiza reservas.</p></footer>
      </div>
    </main>
  </div>
</template>

<style>
:root { font-family: 'Avenir Next', 'Segoe UI', Arial, sans-serif; color: #292239; background: #f6f5f8; font-synthesis: none; }
* { box-sizing: border-box; }
body { margin: 0; }
button, select { font: inherit; }
button, select, summary { cursor: pointer; }
button:focus-visible, select:focus-visible, summary:focus-visible, a:focus-visible { outline: 3px solid #bda0ff; outline-offset: 5px; }
.site-header { background: #300078; color: white; border-bottom: 1px solid #ffffff20; }
.header-content, .hero-content, .main-content { max-width: 1200px; margin: 0 auto; padding-left: 32px; padding-right: 32px; }
.header-content { min-height: 90px; display: flex; align-items: center; justify-content: space-between; gap: 24px; }
.brand { display: inline-flex; align-items: center; gap: 9px; color: white; text-decoration: none; font-size: 30px; font-weight: 750; letter-spacing: -1.2px; }
.demo-badge { font-size: 9px; font-weight: 600; border: 1px solid #ffffff55; border-radius: 5px; padding: 4px 6px; letter-spacing: 1px; margin: 4px 0 0 6px; }
.user-picker { display: flex; align-items: center; gap: 12px; }
.avatar { display: grid; place-items: center; width: 40px; height: 40px; border-radius: 50%; background: #6b3da4; color: white; font-weight: 600; }
.user-picker label { display: block; font-size: 11px; color: #ddd0ef; margin: 0 0 3px 5px; }
.user-picker select { color: white; background: #300078; border: none; border-radius: 4px; padding: 3px 20px 3px 1px; font-size: 14px; font-weight: 600; max-width: 275px; }
.hero { background: #300078; color: white; }
.hero-content { position: relative; padding-top: 42px; padding-bottom: 68px; overflow: hidden; }
.eyebrow { color: #dec8ff; font-size: 10px; font-weight: 700; letter-spacing: 2px; margin: 0 0 17px; }
.eyebrow span { font-size: 19px; vertical-align: middle; margin-right: 7px; }
h1 { margin: 0; font-size: clamp(36px, 4.5vw, 51px); line-height: 1.12; letter-spacing: -1.9px; font-weight: 700; }
h1 span { color: #d0afff; }
.hero-content > p:last-of-type { color: #e1d6f0; font-size: 14px; line-height: 1.7; margin-top: 18px; margin-bottom: 0; }
.hero-stamp { position: absolute; right: 85px; top: 25px; width: 280px; transform: rotate(-8deg); color: #c4a1f7; opacity: .75; }
.hero-stamp svg { width: 100%; height: 195px; }
.hero-stamp span { display: block; text-align: center; font-size: 10px; letter-spacing: 3px; }
.profile-summary { position: relative; margin: -29px 0 42px; padding: 23px 26px; border: 1px solid #e8e4ec; border-radius: 14px; background: white; box-shadow: 0 5px 20px #2c095c06; display: flex; gap: 30px; align-items: center; justify-content: space-between; }
.profile-copy { display: flex; align-items: center; gap: 14px; max-width: 460px; }
.profile-icon { display: grid; place-items: center; color: #6a26c2; background: #f2eaff; border-radius: 12px; font-size: 30px; height: 48px; width: 48px; flex-shrink: 0; }
.profile-copy strong { font-size: 14px; }
.profile-copy p { font-size: 12px; line-height: 1.55; color: #736a80; margin: 5px 0 0; }
.profile-facts { display: flex; gap: 25px; flex-shrink: 0; }
.profile-facts span { display: block; color: #7e748a; font-size: 10px; margin-bottom: 6px; }
.profile-facts strong { font-size: 12px; font-weight: 650; }
.results-heading { display: flex; align-items: end; justify-content: space-between; gap: 20px; margin-bottom: 22px; }
.section-kicker { color: #786988; font-size: 9px; letter-spacing: 1.7px; font-weight: 700; margin: 0 0 7px; }
.results-heading h2 { font-size: 27px; letter-spacing: -.8px; margin: 0; font-weight: 650; }
.results-count { color: #796e89; font-size: 12px; padding-bottom: 4px; white-space: nowrap; }
.package-card { display: grid; grid-template-columns: 180px minmax(0, 1fr) 225px; border: 1px solid #e5e0eb; border-radius: 14px; overflow: hidden; background: white; margin-bottom: 20px; box-shadow: 0 4px 14px #30204704; }
.destination-art { display: flex; flex-direction: column; justify-content: space-between; position: relative; overflow: hidden; padding: 22px 18px; background: #e1f1f0; min-height: 230px; }
.trip-label { font-size: 8px; letter-spacing: 1.4px; color: #27565d; font-weight: 700; position: relative; z-index: 1; }
.landscape { position: absolute; inset: 0; overflow: hidden; }
.sun { position: absolute; height: 70px; width: 70px; background: #ffe4af; border-radius: 50%; top: 52px; right: 20px; }
.hill { position: absolute; width: 300px; height: 190px; border-radius: 50%; transform: rotate(-22deg); }
.hill-back { background: #98cbc5; top: 140px; left: -90px; }
.hill-front { background: #62a6aa; top: 177px; left: -40px; }
.destination-code { z-index: 1; position: relative; margin-top: 100px; color: #103f48; }
.destination-code > span { font-size: 43px; font-weight: 750; letter-spacing: 2px; display: block; }
.destination-code small { font-size: 9px; font-weight: 600; }
.nature { background: #e8eddf; }.nature .hill-back { background: #b1c6a2; }.nature .hill-front { background: #819e80; }.nature .destination-code, .nature .trip-label { color: #233f2d; }
.city { background: #ece6f6; }.city .hill-back { background: #c1b0d9; border-radius: 10px; transform: rotate(8deg); }.city .hill-front { background: #a18bc3; border-radius: 8px; transform: rotate(-8deg); }.city .destination-code, .city .trip-label { color: #392750; }
.package-body { padding: 23px 24px 19px; min-width: 0; }
.package-topline { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; justify-content: space-between; }
.recommendation-label { color: #753bb0; font-size: 9px; font-weight: 700; }
.match { color: #28674c; background: #edf8f1; border-radius: 5px; padding: 5px 7px; font-size: 9px; font-weight: 650; }
.package-body h3 { margin: 13px 0 4px; font-size: 22px; letter-spacing: -.55px; line-height: 1.25; }
.destination { font-size: 11px; color: #7b7186; margin: 0; }
.stay-info { display: flex; gap: 11px; margin: 19px 0 15px; align-items: start; }
.component-icon { color: #7c658d; width: 17px; flex-shrink: 0; font-size: 20px; line-height: 20px; text-align: center; }
.stay-info strong { font-size: 12px; font-weight: 600; }.stay-info p { margin: 4px 0 0; font-size: 10px; color: #7b7186; line-height: 1.5; }
.flight-list { display: grid; gap: 9px; }.flight-row { display: flex; align-items: center; gap: 10px; font-size: 10px; }.flight-direction { width: 30px; color: #73687d; }.flight-row strong { font-size: 10px; white-space: nowrap; }.route-arrow { color: #a194ac; margin: 0 4px; }.flight-schedule { color: #766c80; margin-left: auto; text-align: right; font-size: 10px; }
.package-price { border-left: 1px solid #eeeaf2; padding: 23px 20px; display: flex; flex-direction: column; justify-content: center; align-items: flex-start; }
.included-badge { color: #6c4c89; background: #f5effb; border-radius: 5px; padding: 6px 8px; font-size: 9px; font-weight: 600; margin-bottom: 23px; }
.price-label { font-size: 10px; color: #766b82; margin-bottom: 4px; }.package-price > strong { font-size: 22px; letter-spacing: -.8px; white-space: nowrap; }.package-price p { color: #80748d; font-size: 10px; line-height: 1.65; margin: 8px 0 17px; }.budget-note { color: #357458; font-size: 9px; }.budget-note::before { content: '✓'; padding-right: 5px; }
.package-detail { grid-column: 1 / -1; border-top: 1px solid #eeeaf2; }.package-detail summary { list-style: none; padding: 13px 23px; display: flex; align-items: center; justify-content: space-between; color: #6624a7; font-size: 11px; font-weight: 600; }.package-detail summary::-webkit-details-marker { display: none; }.package-detail summary span { font-size: 15px; }.package-detail[open] summary span { transform: rotate(45deg); }
.detail-content { display: grid; grid-template-columns: 1fr 1fr 1.2fr; gap: 25px; padding: 4px 24px 25px; }.detail-content h4 { font-size: 12px; margin: 12px 0; }.detail-content p, .detail-content small { font-size: 11px; line-height: 1.7; color: #7a6e87; }.detail-content dl { font-size: 11px; color: #6c6277; }.detail-content dl > div { display: flex; justify-content: space-between; gap: 12px; padding: 6px 0; }.detail-content dd { margin: 0; white-space: nowrap; }.breakdown-total { border-top: 1px solid #e8e2ef; font-weight: 700; color: #292239; margin-top: 6px; }
.selection-note { text-align: center; color: #85788f; font-size: 11px; margin: 25px 0 0; }.selection-note span { font-size: 18px; margin-right: 5px; vertical-align: middle; }
.state-card { padding: 32px; margin: 25px 0; border: 1px solid #e5e0eb; border-radius: 14px; background: white; text-align: center; }.state-card h2, .state-card h3 { font-size: 20px; }.state-card p { color: #776c83; font-size: 14px; line-height: 1.6; }.state-card button { background: #6423bc; color: white; border: none; border-radius: 20px; padding: 10px 23px; margin-top: 8px; }.empty-icon { color: #9b7ac2; font-size: 38px; }.loading-label { color: #776c83; font-size: 13px; }.skeleton { border-radius: 14px; display: flex; background: white; margin-bottom: 20px; min-height: 250px; overflow: hidden; }.skeleton > span { width: 180px; background: #ebe5f2; }.skeleton > div { flex: 1; padding: 35px; }.skeleton i { display: block; background: #f1edf5; height: 20px; width: 75%; margin-bottom: 25px; border-radius: 5px; }
footer { display: flex; align-items: center; justify-content: space-between; gap: 25px; border-top: 1px solid #e4deea; margin-top: 50px; padding: 25px 0 30px; }.footer-brand { font-size: 18px; letter-spacing: -.6px; font-weight: 700; color: #80728f; }.footer-brand span { font-size: 10px; font-weight: 400; }.footer-brand, footer p { white-space: normal; }footer p { font-size: 10px; color: #867b91; line-height: 1.6; text-align: right; }
@media (max-width: 1050px) { .profile-summary { align-items: start; flex-direction: column; gap: 20px; }.profile-copy { max-width: none; }.profile-facts { width: 100%; justify-content: space-between; border-top: 1px solid #eeeaf2; padding-top: 16px; }.package-card { grid-template-columns: 145px minmax(0, 1fr) 190px; }.package-price { padding: 20px 15px; }.package-price > strong { font-size: 19px; }.package-body { padding: 20px 18px; }.flight-row { flex-wrap: wrap; gap: 7px; }.flight-schedule { width: 100%; text-align: left; padding-left: 24px; }.destination-art { padding: 20px 13px; } }
@media (max-width: 760px) { .header-content, .hero-content, .main-content { padding-left: 20px; padding-right: 20px; }.hero-stamp { right: 15px; width: 190px; top: 40px; opacity: .35; }.hero-content { padding-top: 34px; padding-bottom: 60px; }.header-content { min-height: 82px; gap: 15px; }.brand { font-size: 23px; }.demo-badge, .avatar { display: none; }.user-picker select { font-size: 12px; max-width: 210px; }.user-picker label { font-size: 9px; }.package-card { grid-template-columns: 130px minmax(0, 1fr); }.package-price { grid-column: 1 / -1; border-left: none; border-top: 1px solid #eeeaf2; padding: 16px 20px; display: grid; grid-template-columns: 1fr 1fr; gap: 5px 15px; }.included-badge { display: none; }.price-label { grid-column: 1; }.package-price > strong { grid-column: 1; grid-row: 2; }.package-price p { grid-column: 2; grid-row: 1 / 3; margin: 0; align-self: center; text-align: right; }.budget-note { grid-column: 1 / -1; margin-top: 3px; }.detail-content { grid-template-columns: 1fr; gap: 5px; }.profile-summary { padding: 20px; }.profile-facts { flex-wrap: wrap; gap: 15px; }.results-heading h2 { font-size: 24px; }.package-body h3 { font-size: 19px; }.match { font-size: 8px; }.destination-code > span { font-size: 36px; }.destination-code small { line-height: 1.6; display: block; }.trip-label { font-size: 7px; }.package-topline { gap: 5px; }.recommendation-label { font-size: 8px; } }
@media (max-width: 480px) { .header-content { flex-wrap: wrap; padding-top: 18px; padding-bottom: 16px; gap: 17px; }.user-picker { width: 100%; }.user-picker > div { width: 100%; display: flex; align-items: center; justify-content: space-between; gap: 10px; }.user-picker label { margin: 0; }.user-picker select { max-width: 205px; }.hero-stamp { display: none; }h1 { font-size: 37px; }.hero-content > p:last-of-type { font-size: 13px; }.package-card { grid-template-columns: 1fr; }.destination-art { min-height: 95px; padding: 15px 20px; flex-direction: row; align-items: center; }.destination-code { margin-top: 0; text-align: right; }.destination-code > span { font-size: 32px; }.destination-code small { font-size: 8px; }.sun { height: 45px; width: 45px; top: 10px; right: 135px; }.hill-back { top: 45px; left: -10px; }.hill-front { top: 85px; left: 60px; }.flight-row { flex-wrap: nowrap; }.flight-schedule { width: auto; padding: 0; text-align: right; font-size: 9px; }.results-heading h2 { font-size: 22px; }.profile-facts strong { font-size: 11px; }.profile-facts span { font-size: 9px; }.profile-copy p { font-size: 11px; }.profile-summary { margin-bottom: 30px; }.selection-note { line-height: 1.7; }footer { align-items: start; flex-direction: column; gap: 7px; }footer p { text-align: left; margin: 0; } }
</style>
