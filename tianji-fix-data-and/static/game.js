document.addEventListener('DOMContentLoaded', () => {
    const socket = io();

    // --- DOM Element References ---
    const elements = {
        startGameBtn: document.getElementById('start-game'),
        nextPhaseBtn: document.getElementById('next-phase'),
        resetGameBtn: document.getElementById('reset-game'),
        player1Name: document.getElementById('player1-name'),
        player1Health: document.getElementById('player1-health'),
        player1Gold: document.getElementById('player1-gold'),
        player1Position: document.getElementById('player1-position'),
        player1Indicator: document.getElementById('player1-indicator'),
        player2Name: document.getElementById('player2-name'),
        player2Health: document.getElementById('player2-health'),
        player2Gold: document.getElementById('player2-gold'),
        player2Position: document.getElementById('player2-position'),
        player2Indicator: document.getElementById('player2-indicator'),
        player1Hand: document.getElementById('player1-hand'),
        player2Hand: document.getElementById('player2-hand'),
        piecesGroup: document.getElementById('player-pieces'),
        juInfo: document.getElementById('ju-info'),
        turnInfo: document.getElementById('turn-info'),
        phaseInfo: document.getElementById('phase-info'),
        gameFundInfo: document.getElementById('game-fund-info'),
        celestialStemCardName: document.querySelector('#celestial-stem-card .card-name'),
        celestialBranchCardName: document.querySelector('#celestial-branch-card .card-name'),
        logMessages: document.getElementById('log-messages'),
        qimenDoorsGroup: document.getElementById('qimen-doors'),
    };

    // --- Static Map Data for Rendering ---
    const mapData = {
        center: { x: 400, y: 400 },
        palaces: [
            { id: 'li',   name: '离', symbol: '☲', luoshu: 9, angle: -22.5 },
            { id: 'kun',  name: '坤', symbol: '☷', luoshu: 2, angle: 22.5 },
            { id: 'dui',  name: '兑', symbol: '☱', luoshu: 7, angle: 67.5 },
            { id: 'qian', name: '乾', symbol: '☰', luoshu: 6, angle: 112.5 },
            { id: 'kan',  name: '坎', symbol: '☵', luoshu: 1, angle: 157.5 },
            { id: 'gen',  name: '艮', symbol: '☶', luoshu: 8, angle: 202.5 },
            { id: 'zhen', name: '震', symbol: '☳', luoshu: 3, angle: 247.5 },
            { id: 'xun',  name: '巽', symbol: '☴', luoshu: 4, angle: 292.5 }
        ],
        departments: [
            { id: 'tian', name: '天', innerRadius: 82,  outerRadius: 148 },
            { id: 'ren',  name: '人', innerRadius: 148, outerRadius: 230 },
            { id: 'di',   name: '地', innerRadius: 230, outerRadius: 313 }
        ],
        zones: {}
    };

    // --- Core UI Update Function ---
    function updateUI(state) {
        console.log("Received game state update:", state);

        if (!state || !state.players || !state.game_board) {
            console.warn("Incomplete state received, skipping UI update.");
            return;
        }
        // Update Player Panels
        state.players.forEach(player => {
            const id = player.player_id;
            const nameEl = document.getElementById(`player${id}-name`);
            if (nameEl) nameEl.textContent = player.name;
            document.getElementById(`player${id}-health`).textContent = player.health;
            document.getElementById(`player${id}-gold`).textContent = player.gold;
            document.getElementById(`player${id}-indicator`).style.opacity = player.player_id === state.active_player_id ? '1' : '0.3';

            const zone = state.game_board.zones[player.position];
            const positionText = zone ? `${zone.palace.toUpperCase()}-${zone.department.toUpperCase()}` : '-';
            document.getElementById(`player${id}-position`).textContent = positionText;

            // Update player hand
            const handEl = document.getElementById(`player${id}-hand`);
            handEl.innerHTML = '';
            player.hand.forEach(card => {
                const cardDiv = document.createElement('div');
                cardDiv.className = 'card';
                cardDiv.textContent = card.name;
                cardDiv.title = card.description;
                handEl.appendChild(cardDiv);
            });
        });

        // Update Player Pieces on Board
        elements.piecesGroup.innerHTML = ''; // Clear old pieces
        state.players.forEach(player => {
            if (player.position && player.position !== 'None' && mapData.zones[player.position] && !player.is_eliminated) {
                const center = mapData.zones[player.position].center;
                const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                circle.setAttribute('cx', center.x);
                circle.setAttribute('cy', center.y);
                circle.setAttribute('r', 12);
                circle.setAttribute('class', `player-piece player-${player.player_id}-piece ${player.player_id === state.active_player_id ? 'current-player' : ''}`);
                elements.piecesGroup.appendChild(circle);
            }
        });

        // Update Game Info
        const dunText = state.dun_type === "YANG" ? "阳遁" : "阴遁";
        elements.juInfo.textContent = `${state.solar_term || '未知节气'} | ${dunText}`;
        elements.turnInfo.textContent = `回合: ${state.current_turn}`;
        elements.phaseInfo.textContent = `阶段: ${state.current_phase}`;
        elements.gameFundInfo.textContent = `奖金池: ${state.game_fund}`;

        // Update Celestial Cards Panel
        const stemCard = state.current_celestial_stem;
        const branchCard = state.current_terrestrial_branch;

        if (stemCard) {
            elements.celestialStemCardName.textContent = stemCard.name;
            elements.celestialStemCardName.parentElement.title = stemCard.description;
        } else {
            elements.celestialStemCardName.textContent = '-';
            elements.celestialStemCardName.parentElement.title = '';
        }

        if (branchCard) {
            elements.celestialBranchCardName.textContent = branchCard.name;
            elements.celestialBranchCardName.parentElement.title = branchCard.description;
        } else {
            elements.celestialBranchCardName.textContent = '-';
            elements.celestialBranchCardName.parentElement.title = '';
        }

        // Update Log
        elements.logMessages.innerHTML = ''; // Clear old logs
        if (state.log_messages && state.log_messages.length > 0) {
            state.log_messages.forEach(msg => {
                const logEntry = document.createElement('p');
                logEntry.className = 'log-message';
                if (msg.includes('VICTORY') || msg.includes('wins')) {
                    logEntry.classList.add('victory');
                } else if (msg.includes('ELIMINATED')) {
                    logEntry.classList.add('elimination');
                } else if (msg.includes('error') || msg.includes('ERROR')) {
                    logEntry.classList.add('error');
                }
                logEntry.textContent = msg;
                elements.logMessages.appendChild(logEntry);
            });
            elements.logMessages.scrollTop = elements.logMessages.scrollHeight;
        }

        // Update Qi Men Gates
        if (state.game_board && state.game_board.qimen_gates) {
            updateQimenGates(state.game_board.qimen_gates);
        }

        // Handle Winner Display
        if (state.winner) {
            let winnerMessage = "";
            if (state.winner === "DRAW") {
                winnerMessage = "游戏结束：平局！";
            } else {
                winnerMessage = `游戏结束：${state.winner.name} 获胜!`;
            }
            const winnerOverlay = document.createElement('div');
            winnerOverlay.className = 'winner-overlay';
            winnerOverlay.textContent = winnerMessage;
            document.body.appendChild(winnerOverlay);
        } else {
            // Remove winner overlay if it exists and game is reset
            const overlay = document.querySelector('.winner-overlay');
            if (overlay) {
                overlay.remove();
            }
        }
    }

    function updateQimenGates(gates) {
        const svgNS = "http://www.w3.org/2000/svg";
        elements.qimenDoorsGroup.innerHTML = '';
        const qimenRadius = (mapData.departments[2].outerRadius + mapData.departments[1].outerRadius) / 2;

        for (const palaceId in gates) {
            if (palaceId === 'ju_number') continue; // Skip the ju_number property
            const gateSymbol = gates[palaceId];
            const palace = mapData.palaces.find(p => p.id === palaceId);
            if (palace) {
                const centerAngle = palace.angle + 22.5;
                const center = polarToCartesian(mapData.center.x, mapData.center.y, qimenRadius, centerAngle);

                const doorGroup = document.createElementNS(svgNS, 'g');
                doorGroup.setAttribute('class', 'qimen-door');
                const circle = document.createElementNS(svgNS, 'circle');
                circle.setAttribute('cx', center.x);
                circle.setAttribute('cy', center.y);
                circle.setAttribute('r', 25);
                circle.setAttribute('class', 'door-circle');
                doorGroup.appendChild(circle);

                const symbol = document.createElementNS(svgNS, 'text');
                symbol.setAttribute('x', center.x);
                symbol.setAttribute('y', center.y);
                symbol.setAttribute('class', 'door-text');
                symbol.textContent = gateSymbol;
                doorGroup.appendChild(symbol);
                elements.qimenDoorsGroup.appendChild(doorGroup);
            }
        }
    }

    // --- Initial Map Drawing (Static part) ---
    function initializeMap() {
        const svgNS = "http://www.w3.org/2000/svg";
        mapData.palaces.forEach(palace => {
            mapData.departments.forEach(dept => {
                const zoneId = `${palace.id}_${dept.id}`;
                const radius = (dept.innerRadius + dept.outerRadius) / 2;
                const centerAngle = palace.angle + 22.5;
                mapData.zones[zoneId] = { center: polarToCartesian(mapData.center.x, mapData.center.y, radius, centerAngle) };
            });
        });
        mapData.zones["zhong_gong"] = { center: { x: 400, y: 400 } };

        const diRing = document.getElementById('di-ring');
        const renRing = document.getElementById('ren-ring');
        const tianRing = document.getElementById('tian-ring');
        mapData.palaces.forEach(palace => {
            mapData.departments.forEach(dept => {
                const path = createAnnulusSector(mapData.center.x, mapData.center.y, dept.innerRadius, dept.outerRadius, palace.angle, palace.angle + 45);
                path.setAttribute('class', `zone gong-${palace.id} bu-${dept.id}`);
                if (dept.id === 'di') diRing.appendChild(path);
                else if (dept.id === 'ren') renRing.appendChild(path);
                else tianRing.appendChild(path);
            });
        });

        const labelsGroup = document.getElementById('text-labels');
        const symbolsGroup = document.getElementById('trigram-symbols-layer');
        mapData.palaces.forEach(palace => {
            const angle = palace.angle + 22.5;
            const isDark = palace.id === 'kan';
            const labelPos = polarToCartesian(mapData.center.x, mapData.center.y, (mapData.departments[1].innerRadius + mapData.departments[1].outerRadius) / 2, angle);
            const text = document.createElementNS(svgNS, 'text');
            text.setAttribute('x', labelPos.x); text.setAttribute('y', labelPos.y); text.setAttribute('dy', '0.35em');
            text.setAttribute('class', isDark ? 'labels label-on-dark' : 'labels');
            text.textContent = palace.name;
            if (angle > 90 && angle < 270) text.setAttribute('transform', `rotate(180 ${labelPos.x} ${labelPos.y})`);
            labelsGroup.appendChild(text);
        });
    }

    function createAnnulusSector(cx, cy, r0, r1, a0, a1) {
        const p0 = polarToCartesian(cx, cy, r0, a0); const p1 = polarToCartesian(cx, cy, r1, a0);
        const p2 = polarToCartesian(cx, cy, r1, a1); const p3 = polarToCartesian(cx, cy, r0, a1);
        const largeArc = a1 - a0 <= 180 ? "0" : "1";
        const d = `M ${p0.x} ${p0.y} L ${p1.x} ${p1.y} A ${r1} ${r1} 0 ${largeArc} 1 ${p2.x} ${p2.y} L ${p3.x} ${p3.y} A ${r0} ${r0} 0 ${largeArc} 0 ${p0.x} ${p0.y} Z`;
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute("d", d);
        return path;
    }

    function polarToCartesian(cx, cy, r, angle) {
        const a = (angle - 90) * Math.PI / 180;
        return { x: cx + (r * Math.cos(a)), y: cy + (r * Math.sin(a)) };
    }

    // --- Socket.IO Event Listeners ---
    socket.on('connect', () => {
        console.log('Connected to server!');
        socket.emit('request_initial_state');
    });
    socket.on('disconnect', () => console.log('Disconnected from server.'));
    socket.on('error', (data) => {
        console.error('Server Error:', data.message);
        const logEntry = document.createElement('p');
        logEntry.className = 'log-message error';
        logEntry.textContent = `ERROR: ${data.message}`;
        elements.logMessages.appendChild(logEntry);
        elements.logMessages.scrollTop = elements.logMessages.scrollHeight;
    });

    socket.on('game_state_update', (state) => {
        updateUI(state);
        const isGameRunning = state.current_phase !== 'SETUP' && state.players && state.players.length > 0;
        const isGameOver = !!state.winner || (state.players && state.players.filter(p => !p.is_eliminated).length <= 1);

        elements.startGameBtn.disabled = isGameRunning;
        elements.nextPhaseBtn.disabled = !isGameRunning || isGameOver;
    });

    // --- Control Button Event Listeners ---
    elements.startGameBtn.addEventListener('click', () => socket.emit('start_game'));
    elements.nextPhaseBtn.addEventListener('click', () => socket.emit('next_phase'));
    elements.resetGameBtn.addEventListener('click', () => {
        socket.emit('reset_game');
        // No need to clear logs here, the updateUI function will handle it.
        const overlay = document.querySelector('.winner-overlay');
        if (overlay) overlay.remove();
    });

    // --- Initial Load ---
    initializeMap();
});