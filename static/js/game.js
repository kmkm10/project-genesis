// Service Workerの登録
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/sw.js').catch(err => {
      console.log('ServiceWorker registration failed: ', err);
    });
  });
}

// これ以降に元々の $(document).ready(...) が続く

$(document).ready(function() {
    // Service Workerの登録
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/static/sw.js').catch(err => console.log('SW reg failed:', err));
        });
    }

    // 1秒ごとにゲームの状態を更新
    setInterval(updateGameView, 1000);
    updateGameView(); // 初回ロード時にも実行

    // --- イベントリスナー ---

    // 汎用アクションボタン (研究/施設)
    $(document).on('click', '.action-btn', function() {
        sendAction({ action: $(this).data('action'), id: $(this).data('id') });
    });

    // ジェネシス・シフト
    $('#genesis-shift-btn').on('click', function() {
        if (confirm('本当にジェネシス・シフトを実行しますか？現在の進捗はリセットされますが、EPを獲得できます。')) {
            $.post('/api/genesis_shift', handleAjaxResponse).fail(handleAjaxError);
        }
    });

    // --- モーダル制御 ---
    const permUpgradeModal = $('#perm-upgrade-modal');
    const dashboardModal = $('#dashboard-modal');

    // EP強化モーダル
    $('#perm-upgrade-btn').on('click', () => permUpgradeModal.show());
    permUpgradeModal.find('.close-btn').on('click', () => permUpgradeModal.hide());

    // ダッシュボードモーダル
    $('#dashboard-btn').on('click', () => dashboardModal.show());
    dashboardModal.find('.close-btn').on('click', () => dashboardModal.hide());
    
    // モーダル外クリックで閉じる
    $(window).on('click', event => {
        if ($(event.target).is(permUpgradeModal)) permUpgradeModal.hide();
        if ($(event.target).is(dashboardModal)) dashboardModal.hide();
    });

    // 永続強化購入ボタン
    $(document).on('click', '.purchase-perm-upgrade-btn', function() {
        $.ajax({
            url: '/api/purchase_permanent_upgrade',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ upgrade_id: $(this).data('id') }),
            success: handleAjaxResponse,
            error: handleAjaxError
        });
    });
});

// --- 関数定義 ---

function updateGameView() {
    $.get('/api/gamestate', data => {
        // メインUI
        $('#rp-count').text(data.research_points.toFixed(2));
        $('#rp-rate').text('+' + data.rp_per_second.toFixed(2) + '/s');
        $('#money-count').text(data.money.toFixed(2));
        $('#money-rate').text('+' + data.money_per_second.toFixed(2) + '/s');
        $('#civ-name').text(data.civilization.name);
        $('#ep-count').text(data.evolution_points.toFixed(0));
        $('#shifts-count').text(data.genesis_shifts);
        $('#genesis-shift-btn').prop('disabled', !data.unlocked_technologies.includes('astronomy'));

        // パネル更新
        updateResearchPanel(data);
        updateFacilityPanel(data);

        // モーダル更新
        updatePermUpgradeModal(data);
        updateDashboardModal(data.dashboard_stats);

        // ログ
        updateLogPanel(data.log);
    }).fail(handleAjaxError);
}

function updateDashboardModal(stats) {
    if (!stats) return;
    const time = stats.time_elapsed_this_run;
    const hours = Math.floor(time / 3600).toString().padStart(2, '0');
    const minutes = Math.floor((time % 3600) / 60).toString().padStart(2, '0');
    const seconds = Math.floor(time % 60).toString().padStart(2, '0');
    $('#stat-time-elapsed').text(`${hours}:${minutes}:${seconds}`);

    $('#stat-total-rp-run').text(stats.total_rp_this_run.toFixed(0));
    $('#stat-unlocked-tech').text(stats.unlocked_tech_count);
    $('#stat-total-tech').text(stats.total_tech_count);
    $('#stat-total-facility-level').text(stats.total_facility_levels);
}

function updateResearchPanel(data) {
    if (data.researching_tech) {
        const [techId, startTime, duration] = data.researching_tech;
        const remaining = duration - (Date.now() / 1000 - startTime);
        const techName = (TECHNOLOGIES[techId] || { name: '不明な研究' }).name;
        $('#research-status').html(`研究中: <strong>${techName}</strong> (残り ${Math.max(0, remaining).toFixed(1)}秒)`);
        $('#research-buttons').hide();
    } else {
        $('#research-status').html('待機中');
        $('#research-buttons').show();
        const researchButtons = $('#research-buttons');
        researchButtons.empty();
        data.available_technologies.forEach(tech => {
            const canAfford = data.research_points >= tech.cost;
            const button = `
                <button class="action-btn" data-action="start_research" data-id="${tech.id}" ${!canAfford ? 'disabled' : ''}>
                    <strong>${tech.name}</strong>
                    <small>コスト: ${tech.cost} RP / 時間: ${tech.time}s</small>
                </button>`;
            researchButtons.append(button);
        });
    }
}

function updateFacilityPanel(data) {
    const facilityButtons = $('#facility-buttons');
    facilityButtons.empty();
    data.facilities.forEach(fac => {
        const canAfford = data.money >= fac.cost;
        const button = `
            <button class="action-btn" data-action="upgrade_facility" data-id="${fac.id}" ${!canAfford ? 'disabled' : ''}>
                <strong>${fac.name} (Lv.${fac.level})</strong>
                <small>拡張コスト: ${fac.cost.toFixed(0)} $</small>
            </button>`;
        facilityButtons.append(button);
    });
}

function updatePermUpgradeModal(data) {
    const upgradeList = $('#perm-upgrade-list');
    $('#modal-ep-count').text(data.evolution_points.toFixed(0));
    upgradeList.empty();
    data.permanent_upgrades.forEach(up => {
        const canAfford = data.evolution_points >= up.cost;
        const itemHTML = `
            <div class="upgrade-item">
                <button class="purchase-perm-upgrade-btn" data-id="${up.id}" ${!canAfford ? 'disabled' : ''}>
                    コスト: ${up.cost} EP
                </button>
                <h4>${up.name} (Lv.${up.level})</h4>
                <p>${up.description}</p>
            </div>
        `;
        upgradeList.append(itemHTML);
    });
}

function updateLogPanel(logEntries) {
    if (logEntries && logEntries.length > 0) {
        const logList = $('#log-list');
        logEntries.forEach(entry => {
            logList.prepend(`<li>${entry}</li>`);
            if (logList.children().length > 10) {
                logList.children().last().remove();
            }
        });
    }
}

function sendAction(payload) {
    $.ajax({
        url: '/api/action',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(payload),
        success: handleAjaxResponse,
        error: handleAjaxError
    });
}

function handleAjaxResponse(response) {
    if (response.success) {
        updateGameView();
        if (response.message) {
            alert(response.message);
        }
    } else {
        alert("エラー: " + (response.message || "不明なエラーが発生しました。"));
    }
}

function handleAjaxError(jqXHR, textStatus, errorThrown) {
    console.error("AJAX Error:", textStatus, errorThrown, jqXHR.responseText);
    if (jqXHR.status === 401 || jqXHR.status === 404) {
        alert("セッションが切れました。ログインページに戻ります。");
        window.location.href = '/login';
    }
}

// サーバーから送られてこない研究中の技術名を補完するための参照用データ
const TECHNOLOGIES = { 'fire': { 'name': '火の発見' }, 'stone_tools': { 'name': '石器' }, 'agriculture': { 'name': '農耕' }, 'writing': { 'name': '文字' }, 'calculus': { 'name': '微積分学' }, 'optics': { 'name': '光学' }, 'astronomy': { 'name': '天文学' } };
