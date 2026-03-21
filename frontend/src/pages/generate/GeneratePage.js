import useGenerateForm from './hooks/useGenerateForm';
import useGeneration from './hooks/useGeneration';
import VoiceSourceSection from './sections/VoiceSourceSection';
import TextParamsSection from './sections/TextParamsSection';
import GenerateButton from './sections/GenerateButton';
import OutputSection from './sections/OutputSection';

export default function GeneratePage() {
  const form = useGenerateForm();
  const gen = useGeneration();

  const handleGenerate = () => {
    if (!form.canGenerate || gen.isGenerating) return;
    gen.generate(form.buildParams(), form.mode);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-5">
      <VoiceSourceSection
        file={form.file}
        onFileSelect={form.setFile}
        onRemove={form.clearFile}
        voiceId={form.voiceId}
        onSelectVoice={form.selectVoice}
        onClearVoice={form.clearVoice}
      />

      <TextParamsSection
        text={form.text} onTextChange={form.setText}
        speed={form.speed} onSpeedChange={form.setSpeed}
        showAdvanced={form.showAdvanced} onToggleAdvanced={form.toggleAdvanced}
        advanced={form.advanced} onAdvancedChange={form.updateAdvanced}
      />

      <GenerateButton
        mode={form.mode} onModeChange={form.setMode}
        isGenerating={gen.isGenerating} streamStage={gen.streamStage}
        canGenerate={form.canGenerate} onGenerate={handleGenerate}
      />

      <OutputSection
        error={gen.error} resultUrl={gen.resultUrl}
        streamChunks={gen.streamChunks} isStreaming={gen.isStreaming}
        streamStage={gen.streamStage}
      />
    </div>
  );
}
