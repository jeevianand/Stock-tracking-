// ---------- POPUP HELPER ----------
function showPopup(message) {
    const popup = document.getElementById("popup");
    if (!popup) return;
    popup.innerText = message;
    popup.style.display = "block";
    setTimeout(() => {
        popup.style.display = "none";
    }, 4000);
}

// ---------- ADD TRADE ----------
document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("tradeForm");
    if (form) {
        form.addEventListener("submit", function (e) {
            e.preventDefault();

            const payload = {
                symbol: document.getElementById("symbol").value,
                buy_price: document.getElementById("buy_price").value,
                sell_price: document.getElementById("sell_price").value,
                quantity: document.getElementById("quantity").value,
                trade_datetime: document.getElementById("trade_datetime").value,
                reason: document.getElementById("reason").value,
                emotion: document.getElementById("emotion").value,
                strategy: document.getElementById("strategy").value,
                notes: document.getElementById("notes").value
            };

            fetch("/api/add_trade", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                showPopup(data.message + " (P/L: " + data.profit + ")");
                form.reset();
            })
            .catch(err => {
                console.error(err);
                showPopup("Something went wrong while saving the trade.");
            });
        });
    }
});

// ---------- LOAD TRADES FOR HISTORY PAGE ----------
function loadTrades() {
    const tbody = document.getElementById("tradesTableBody");
    if (!tbody) return;

    const symbol = document.getElementById("filter_symbol").value;
    const strategy = document.getElementById("filter_strategy").value;
    const emotion = document.getElementById("filter_emotion").value;
    const outcome = document.getElementById("filter_outcome").value;
    const dateFrom = document.getElementById("filter_date_from").value;
    const dateTo = document.getElementById("filter_date_to").value;

    const params = new URLSearchParams();
    if (symbol) params.append("symbol", symbol);
    if (strategy) params.append("strategy", strategy);
    if (emotion) params.append("emotion", emotion);
    if (outcome) params.append("outcome", outcome);
    if (dateFrom) params.append("date_from", dateFrom);
    if (dateTo) params.append("date_to", dateTo);

    fetch("/api/trades?" + params.toString())
        .then(res => res.json())
        .then(trades => {
            tbody.innerHTML = "";
            trades.forEach(t => {
                const tr = document.createElement("tr");

                const dt = new Date(t.trade_datetime);
                const dtStr = dt.toLocaleString();

                tr.innerHTML = `
                    <td>${dtStr}</td>
                    <td>${t.symbol}</td>
                    <td>${t.buy_price}</td>
                    <td>${t.sell_price}</td>
                    <td>${t.quantity}</td>
                    <td style="color:${t.profit > 0 ? '#22c55e' : (t.profit < 0 ? '#ef4444' : '#e5e7eb')}">
                        ${t.profit}
                    </td>
                    <td>${t.emotion || ""}</td>
                    <td>${t.strategy || ""}</td>
                    <td>${t.reason || ""}</td>
                    <td>${t.notes || ""}</td>
                `;
                tbody.appendChild(tr);
            });
        })
        .catch(err => {
            console.error(err);
            showPopup("Error loading trades.");
        });
}

// ---------- LOAD DASHBOARD ----------
function loadDashboard() {
    fetch("/api/dashboard")
        .then(res => res.json())
        .then(data => {
            const totalTradesEl = document.getElementById("total_trades");
            const totalProfitEl = document.getElementById("total_profit");
            const winRateEl = document.getElementById("win_rate");
            const avgWL = document.getElementById("avg_wins_losses");

            if (totalTradesEl) totalTradesEl.innerText = data.total_trades;
            if (totalProfitEl) totalProfitEl.innerText = data.total_profit;
            if (winRateEl) winRateEl.innerText = data.win_rate.toFixed(2) + "%";
            if (avgWL) avgWL.innerText = data.avg_win.toFixed(2) + " / " + data.avg_loss.toFixed(2);

            const listSymbol = document.getElementById("profit_by_symbol");
            const listStrategy = document.getElementById("profit_by_strategy");
            const listEmotion = document.getElementById("profit_by_emotion");

            if (listSymbol) {
                listSymbol.innerHTML = "";
                data.profit_by_symbol.forEach(item => {
                    const li = document.createElement("li");
                    li.textContent = `${item.symbol || "Unknown"} : ${item.profit}`;
                    listSymbol.appendChild(li);
                });
            }

            if (listStrategy) {
                listStrategy.innerHTML = "";
                data.profit_by_strategy.forEach(item => {
                    const li = document.createElement("li");
                    li.textContent = `${item.strategy || "No strategy"} : ${item.profit}`;
                    listStrategy.appendChild(li);
                });
            }

            if (listEmotion) {
                listEmotion.innerHTML = "";
                data.profit_by_emotion.forEach(item => {
                    const li = document.createElement("li");
                    li.textContent = `${item.emotion || "No emotion"} : ${item.profit}`;
                    listEmotion.appendChild(li);
                });
            }
        })
        .catch(err => {
            console.error(err);
            showPopup("Error loading dashboard.");
        });
}
