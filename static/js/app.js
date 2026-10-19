document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const scriptText = document.getElementById('script-text');
  const scriptCounter = document.getElementById('script-counter');
  const voiceSelect = document.getElementById('voice-select');
  const btnPreviewAudio = document.getElementById('btn-preview-audio');
  const audioPlayer = document.getElementById('audio-player');
  const emotionSelect = document.getElementById('emotion-select');
  const gestureMode = document.getElementById('gesture-mode');
  const gestureIntensity = document.getElementById('gesture-intensity');
  const intensityVal = document.getElementById('intensity-val');
  const resolutionSelect = document.getElementById('resolution-select');
  const btnGenerate = document.getElementById('btn-generate');

  const progressContainer = document.getElementById('progress-container');
  const progressStatus = document.getElementById('progress-status');
  const progressPercent = document.getElementById('progress-percent');
  const progressFill = document.getElementById('progress-fill');

  const playerPlaceholder = document.getElementById('player-placeholder');
  const outputVideo = document.getElementById('output-video');
  const telemetryBar = document.getElementById('telemetry-bar');
  const telDuration = document.getElementById('tel-duration');
  const telFrames = document.getElementById('tel-frames');
  const telTime = document.getElementById('tel-time');
  const telStress = document.getElementById('tel-stress');
  const btnDownload = document.getElementById('btn-download');

  const avatarGrid = document.getElementById('avatar-grid');
  const backgroundGrid = document.getElementById('background-grid');
  const avatarFileInput = document.getElementById('avatar-file-input');

  const btnPrinciples = document.getElementById('btn-principles');
  const modalPrinciples = document.getElementById('modal-principles');
  const btnCloseModal = document.getElementById('btn-close-modal');

  let selectedAvatarId = 'sophia';
  let selectedBgId = 'modern_office.jpg';

  // 1. Script Word & Duration Counter
  scriptText.addEventListener('input', () => {
    const text = scriptText.value.trim();
    const words = text ? text.split(/\s+/).length : 0;
    // Average speaking speed ~140 words per minute -> ~2.3 words/sec
    const estSeconds = Math.max(1, Math.round(words / 2.3));
    scriptCounter.textContent = `${words} words • ~${estSeconds}s`;
  });

  // 2. Gesture Intensity Slider
  gestureIntensity.addEventListener('input', () => {
    intensityVal.textContent = `${gestureIntensity.value}x`;
  });

  // 3. Load Initial Data
  loadVoices();
  loadAvatars();
  loadBackgrounds();

  async function loadVoices() {
    try {
      const res = await fetch('/api/voices');
      const voices = await res.json();
      voiceSelect.innerHTML = voices.map(v => `
        <option value="${v.id}">${v.name}</option>
      `).join('');
    } catch (err) {
      console.error('Failed to load voices:', err);
    }
  }

  async function loadAvatars() {
    try {
      const res = await fetch('/api/avatars');
      const avatars = await res.json();
      avatarGrid.innerHTML = avatars.map((av, idx) => `
        <div class="avatar-card ${av.id === selectedAvatarId ? 'active' : ''}" data-id="${av.id}">
          <img src="${av.preview_url}?t=${Date.now()}" alt="${av.name}">
          <span class="name">${av.name.split(' ')[0]}</span>
        </div>
      `).join('');

      document.querySelectorAll('.avatar-card').forEach(card => {
        card.addEventListener('click', () => {
          document.querySelectorAll('.avatar-card').forEach(c => c.classList.remove('active'));
          card.classList.add('active');
          selectedAvatarId = card.dataset.id;
        });
      });
    } catch (err) {
      console.error('Failed to load avatars:', err);
    }
  }

  async function loadBackgrounds() {
    try {
      const res = await fetch('/api/backgrounds');
      const backgrounds = await res.json();
      backgroundGrid.innerHTML = backgrounds.map(bg => `
        <div class="bg-card ${bg.id === selectedBgId ? 'active' : ''}" data-id="${bg.id}">
          <img src="${bg.url}" alt="${bg.name}">
          <span class="name">${bg.name}</span>
        </div>
      `).join('');

      document.querySelectorAll('.bg-card').forEach(card => {
        card.addEventListener('click', () => {
          document.querySelectorAll('.bg-card').forEach(c => c.classList.remove('active'));
          card.classList.add('active');
          selectedBgId = card.dataset.id;
        });
      });
    } catch (err) {
      console.error('Failed to load backgrounds:', err);
    }
  }

  // 4. Voice Preview
  btnPreviewAudio.addEventListener('click', async () => {
    const text = scriptText.value.trim() || 'Hello, welcome to HeyGen Local Studio.';
    btnPreviewAudio.disabled = true;
    btnPreviewAudio.textContent = 'Synthesizing...';

    try {
      const res = await fetch('/api/preview-audio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          script: text,
          voice_id: voiceSelect.value
        })
      });

      const data = await res.json();
      if (data.status === 'success') {
        audioPlayer.src = data.audio_url;
        audioPlayer.play();
      } else {
        alert(data.detail || 'Voice preview failed.');
      }
    } catch (err) {
      alert('Error connecting to backend: ' + err.message);
    } finally {
      btnPreviewAudio.disabled = false;
      btnPreviewAudio.innerHTML = `
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/></svg>
        Preview
      `;
    }
  });

  // 5. Upload Custom Portrait
  avatarFileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const name = prompt('Enter a name for this custom avatar:', 'My Avatar') || 'Custom Persona';
    const formData = new FormData();
    formData.append('name', name);
    formData.append('file', file);

    try {
      const res = await fetch('/api/upload-avatar', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (data.status === 'success') {
        selectedAvatarId = data.avatar.id;
        await loadAvatars();
      } else {
        alert(data.detail || 'Failed to process custom portrait.');
      }
    } catch (err) {
      alert('Error uploading portrait: ' + err.message);
    }
  });

  // 6. Generate Video
  btnGenerate.addEventListener('click', async () => {
    const script = scriptText.value.trim();
    if (!script) {
      alert('Please enter a script before generating video.');
      scriptText.focus();
      return;
    }

    btnGenerate.disabled = true;
    progressContainer.style.display = 'block';
    progressFill.style.width = '10%';
    progressPercent.textContent = '10%';
    progressStatus.textContent = 'Synthesizing voice & acoustic prosody...';

    // Simulate progressive stages
    const timer = setInterval(() => {
      const current = parseInt(progressFill.style.width);
      if (current < 45) {
        progressFill.style.width = `${current + 10}%`;
        progressPercent.textContent = `${current + 10}%`;
      } else if (current < 85) {
        progressStatus.textContent = 'Rendering lip-sync, micro-expressions & hand kinematics...';
        progressFill.style.width = `${current + 5}%`;
        progressPercent.textContent = `${current + 5}%`;
      }
    }, 600);

    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          script: script,
          avatar_id: selectedAvatarId,
          voice_id: voiceSelect.value,
          emotion: emotionSelect.value,
          gesture_mode: gestureMode.value,
          gesture_intensity: parseFloat(gestureIntensity.value),
          background_id: selectedBgId,
          resolution: resolutionSelect.value
        })
      });

      clearInterval(timer);
      const data = await res.json();

      if (data.status === 'success') {
        progressFill.style.width = '100%';
        progressPercent.textContent = '100%';
        progressStatus.textContent = 'Completed!';

        setTimeout(() => {
          progressContainer.style.display = 'none';
        }, 1200);

        // Display video
        playerPlaceholder.style.display = 'none';
        outputVideo.style.display = 'block';
        outputVideo.src = data.video_url;
        outputVideo.load();
        outputVideo.play();

        // Telemetry
        telemetryBar.style.display = 'flex';
        telDuration.textContent = `${data.metadata.duration}s`;
        telFrames.textContent = data.metadata.total_frames;
        telTime.textContent = `${data.metadata.processing_time}s`;
        telStress.textContent = data.metadata.stress_peaks_count;
        btnDownload.href = data.video_url;

      } else {
        clearInterval(timer);
        progressContainer.style.display = 'none';
        alert('Generation failed: ' + (data.detail || 'Unknown error'));
      }
    } catch (err) {
      clearInterval(timer);
      progressContainer.style.display = 'none';
      alert('Error during video generation: ' + err.message);
    } finally {
      btnGenerate.disabled = false;
    }
  });

  // 7. Technical Principles Modal
  btnPrinciples.addEventListener('click', () => {
    modalPrinciples.style.display = 'flex';
  });

  btnCloseModal.addEventListener('click', () => {
    modalPrinciples.style.display = 'none';
  });

  modalPrinciples.addEventListener('click', (e) => {
    if (e.target === modalPrinciples) {
      modalPrinciples.style.display = 'none';
    }
  });
});
