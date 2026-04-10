import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'

import { PageHeader } from '../components/PageHeader'
import { QueryState } from '../components/QueryState'
import { api } from '../lib/api'
import { formatMoney } from '../lib/format'

export function ExpensesPage() {
  const queryClient = useQueryClient()
  const [amount, setAmount] = useState('')
  const [category, setCategory] = useState('general')
  const [merchantMode, setMerchantMode] = useState('custom')
  const [merchant, setMerchant] = useState('')
  const [currency, setCurrency] = useState('MXN')
  const [note, setNote] = useState('')
  const [loggedAt, setLoggedAt] = useState('')
  const [budgetAmount, setBudgetAmount] = useState('')
  const [budgetCategory, setBudgetCategory] = useState('')
  const [budgetCurrency, setBudgetCurrency] = useState('MXN')
  const [budgetPeriod, setBudgetPeriod] = useState('weekly')

  const query = useQuery({
    queryKey: ['expenses'],
    queryFn: () => api.getExpenses(),
  })
  const metaQuery = useQuery({
    queryKey: ['expense-meta'],
    queryFn: () => api.getExpenseMeta(),
  })
  const summaryQuery = useQuery({
    queryKey: ['spending-summary', currency],
    queryFn: () => api.getSpendingSummary(undefined, currency),
  })
  const budgetQuery = useQuery({
    queryKey: ['budget-status', budgetPeriod],
    queryFn: () => api.getBudgetStatus(budgetPeriod),
  })

  const merchantOptions = metaQuery.data?.merchants ?? []
  const categoryOptions = metaQuery.data?.categories ?? ['general']
  const currencyOptions = metaQuery.data?.currencies ?? ['MXN', 'USD']
  const periodOptions = metaQuery.data?.periods ?? ['daily', 'weekly', 'monthly']

  const createExpense = useMutation({
    mutationFn: () =>
      api.createExpense({
        amount: Number(amount),
        category: category || null,
        merchant: merchant || null,
        currency,
        note: note || null,
        logged_at: loggedAt || null,
      }),
    onSuccess: async () => {
      setAmount('')
      setCategory('general')
      setMerchantMode('custom')
      setMerchant('')
      setNote('')
      setLoggedAt('')
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['expenses'] }),
        queryClient.invalidateQueries({ queryKey: ['expense-meta'] }),
        queryClient.invalidateQueries({ queryKey: ['spending-summary'] }),
        queryClient.invalidateQueries({ queryKey: ['budget-status'] }),
        queryClient.invalidateQueries({ queryKey: ['daily-status'] }),
      ])
    },
  })

  const deleteExpense = useMutation({
    mutationFn: (expenseId: number) => api.deleteExpense(expenseId),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['expenses'] }),
        queryClient.invalidateQueries({ queryKey: ['expense-meta'] }),
        queryClient.invalidateQueries({ queryKey: ['spending-summary'] }),
        queryClient.invalidateQueries({ queryKey: ['budget-status'] }),
        queryClient.invalidateQueries({ queryKey: ['daily-status'] }),
      ])
    },
  })

  const createBudgetTarget = useMutation({
    mutationFn: () =>
      api.createBudgetTarget({
        amount: Number(budgetAmount),
        period: budgetPeriod,
        category: budgetCategory || null,
        currency: budgetCurrency,
      }),
    onSuccess: async () => {
      setBudgetAmount('')
      setBudgetCategory('')
      await queryClient.invalidateQueries({ queryKey: ['budget-status'] })
    },
  })

  const summaryCategories = useMemo(
    () => Object.entries(summaryQuery.data?.by_category ?? {}),
    [summaryQuery.data?.by_category],
  )

  return (
    <section className="page">
      <PageHeader
        eyebrow="Personal"
        title="Gastos"
        description="Alta manual, resumen del día, presupuesto y borrado de movimientos desde la UI."
      />

      <div className="grid grid--cards">
        <article className="card">
          <div className="stat-card__label">Gasto del día</div>
          <div className="stat-card__value">
            {summaryQuery.data
              ? formatMoney(summaryQuery.data.total_amount, summaryQuery.data.currency)
              : '—'}
          </div>
          <div className="stat-card__hint">
            {summaryQuery.data?.transaction_count ?? 0} movimientos
          </div>
        </article>
        <article className="card">
          <div className="stat-card__label">Presupuestos activos</div>
          <div className="stat-card__value">{budgetQuery.data?.items.length ?? 0}</div>
          <div className="stat-card__hint">{budgetPeriod}</div>
        </article>
        <article className="card">
          <div className="stat-card__label">Categorías usadas hoy</div>
          <div className="stat-card__value">{summaryCategories.length}</div>
          <div className="stat-card__hint">
            {summaryCategories.slice(0, 2).map(([name]) => name).join(', ') || 'Sin categorías'}
          </div>
        </article>
      </div>

      <div className="split">
        <article className="card">
          <h3>Nuevo gasto</h3>
          <form
            className="stack"
            onSubmit={(event) => {
              event.preventDefault()
              if (!amount || Number(amount) <= 0) {
                return
              }
              createExpense.mutate()
            }}
          >
            <div className="form-grid">
              <div className="field">
                <label htmlFor="expense-amount">Monto</label>
                <input
                  id="expense-amount"
                  inputMode="decimal"
                  min="0"
                  onChange={(event) => setAmount(event.target.value)}
                  placeholder="250"
                  step="0.01"
                  type="number"
                  value={amount}
                />
              </div>

              <div className="field">
                <label htmlFor="expense-category">Categoría</label>
                <select
                  id="expense-category"
                  onChange={(event) => setCategory(event.target.value)}
                  value={category}
                >
                  {categoryOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </div>

              <div className="field">
                <label htmlFor="expense-currency">Moneda</label>
                <select
                  id="expense-currency"
                  onChange={(event) => setCurrency(event.target.value)}
                  value={currency}
                >
                  {currencyOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </div>

              <div className="field">
                <label htmlFor="expense-datetime">Fecha y hora</label>
                <input
                  id="expense-datetime"
                  onChange={(event) => setLoggedAt(event.target.value)}
                  type="datetime-local"
                  value={loggedAt}
                />
              </div>
            </div>

            <div className="form-grid">
              <div className="field">
                <label htmlFor="merchant-mode">Merchant</label>
                <select
                  id="merchant-mode"
                  onChange={(event) => {
                    setMerchantMode(event.target.value)
                    if (event.target.value === 'custom') {
                      setMerchant('')
                    }
                  }}
                  value={merchantMode}
                >
                  <option value="custom">Capturar manualmente</option>
                  {merchantOptions.length > 0 ? <option value="existing">Elegir existente</option> : null}
                </select>
              </div>

              {merchantMode === 'existing' && merchantOptions.length > 0 ? (
                <div className="field">
                  <label htmlFor="expense-merchant-existing">Merchant existente</label>
                  <select
                    id="expense-merchant-existing"
                    onChange={(event) => setMerchant(event.target.value)}
                    value={merchant}
                  >
                    <option value="">Selecciona</option>
                    {merchantOptions.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                </div>
              ) : (
                <div className="field">
                  <label htmlFor="expense-merchant">Merchant manual</label>
                  <input
                    id="expense-merchant"
                    onChange={(event) => setMerchant(event.target.value)}
                    placeholder="Amazon, Oxxo, Farmacia Roma…"
                    value={merchant}
                  />
                </div>
              )}
            </div>

            <div className="field">
              <label htmlFor="expense-note">Nota</label>
              <textarea
                id="expense-note"
                onChange={(event) => setNote(event.target.value)}
                placeholder="Contexto opcional"
                value={note}
              />
            </div>

            <div className="actions">
              <button className="button" disabled={createExpense.isPending} type="submit">
                {createExpense.isPending ? 'Guardando…' : 'Guardar gasto'}
              </button>
            </div>
          </form>
        </article>

        <article className="card">
          <h3>Budget target</h3>
          <form
            className="stack"
            onSubmit={(event) => {
              event.preventDefault()
              if (!budgetAmount || Number(budgetAmount) <= 0) {
                return
              }
              createBudgetTarget.mutate()
            }}
          >
            <div className="form-grid">
              <div className="field">
                <label htmlFor="budget-amount">Monto</label>
                <input
                  id="budget-amount"
                  inputMode="decimal"
                  min="0"
                  onChange={(event) => setBudgetAmount(event.target.value)}
                  step="0.01"
                  type="number"
                  value={budgetAmount}
                />
              </div>
              <div className="field">
                <label htmlFor="budget-period">Periodo</label>
                <select
                  id="budget-period"
                  onChange={(event) => setBudgetPeriod(event.target.value)}
                  value={budgetPeriod}
                >
                  {periodOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label htmlFor="budget-category">Categoría</label>
                <select
                  id="budget-category"
                  onChange={(event) => setBudgetCategory(event.target.value)}
                  value={budgetCategory}
                >
                  <option value="">General</option>
                  {categoryOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label htmlFor="budget-currency">Moneda</label>
                <select
                  id="budget-currency"
                  onChange={(event) => setBudgetCurrency(event.target.value)}
                  value={budgetCurrency}
                >
                  {currencyOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="actions">
              <button className="button button--secondary" disabled={createBudgetTarget.isPending} type="submit">
                {createBudgetTarget.isPending ? 'Guardando…' : 'Guardar presupuesto'}
              </button>
            </div>
          </form>

          <QueryState
            isLoading={budgetQuery.isLoading}
            error={budgetQuery.error}
            empty={!budgetQuery.data || budgetQuery.data.items.length === 0}
            emptyMessage="No hay presupuestos configurados para este periodo."
          >
            <ul className="list">
              {budgetQuery.data?.items.map((item) => (
                <li className="list__item" key={`${item.period}-${item.category ?? 'general'}-${item.currency}`}>
                  <p className="list__item-title">{item.category ?? 'general'}</p>
                  <p className="list__item-meta">
                    target {formatMoney(item.target_amount, item.currency)} · actual{' '}
                    {formatMoney(item.actual_amount, item.currency)} · restante{' '}
                    {formatMoney(item.remaining_amount, item.currency)}
                  </p>
                </li>
              ))}
            </ul>
          </QueryState>
        </article>
      </div>

      <div className="split">
        <article className="card">
          <h3>Resumen por categoría</h3>
          <QueryState
            isLoading={summaryQuery.isLoading}
            error={summaryQuery.error}
            empty={!summaryQuery.data || summaryCategories.length === 0}
            emptyMessage="No hay gasto registrado para la fecha actual."
          >
            <ul className="list">
              {summaryCategories.map(([name, total]) => (
                <li className="list__item" key={name}>
                  <p className="list__item-title">{name}</p>
                  <p className="list__item-meta">
                    {formatMoney(total, summaryQuery.data?.currency ?? currency)}
                  </p>
                </li>
              ))}
            </ul>
          </QueryState>
        </article>

        <article className="card">
          <h3>Historial</h3>
          <QueryState
            isLoading={query.isLoading}
            error={query.error}
            empty={!query.data || query.data.length === 0}
          >
            <div className="stack">
              {query.data?.map((row, index) => {
                const expenseId =
                  typeof row.id === 'number'
                    ? row.id
                    : typeof row.id === 'string'
                      ? Number.parseInt(row.id, 10)
                      : index

                return (
                  <div className="list__item" key={`${row.id ?? index}`}>
                    <div className="toolbar">
                      <div>
                        <p className="list__item-title">
                          {formatMoney(Number(row.amount ?? 0), String(row.currency ?? currency))}
                        </p>
                        <p className="list__item-meta">
                          {String(row.category ?? 'general')} · {String(row.merchant ?? 'sin merchant')} ·{' '}
                          {String(row.logged_at ?? '')}
                        </p>
                        {row.note ? <p className="list__item-meta">{String(row.note)}</p> : null}
                      </div>
                      <button
                        className="button button--ghost"
                        disabled={deleteExpense.isPending}
                        onClick={() => deleteExpense.mutate(expenseId)}
                        type="button"
                      >
                        Eliminar
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          </QueryState>
        </article>
      </div>
    </section>
  )
}
