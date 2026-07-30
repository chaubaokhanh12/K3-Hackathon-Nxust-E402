import { useState } from 'react'
import ServerRail from './components/ServerRail.jsx'
import ChannelSidebar from './components/ChannelSidebar.jsx'
import ChannelHeader from './components/ChannelHeader.jsx'
import HoiDapChannel from './components/HoiDapChannel.jsx'
import GeneralChannel from './components/GeneralChannel.jsx'
import ForumChannel from './components/ForumChannel.jsx'
import InfoChannel from './components/InfoChannel.jsx'
import PlaceholderChannel from './components/PlaceholderChannel.jsx'
import MemberList from './components/MemberList.jsx'
import { getChannel } from './data/channels.js'

export default function App() {
  const [activeChannelId, setActiveChannelId] = useState('hoi-dap')
  const [openForumPostId, setOpenForumPostId] = useState(null)
  const [resolvedCount, setResolvedCount] = useState(0)
  const [threadResolved, setThreadResolved] = useState(false)
  const [showMembers, setShowMembers] = useState(true)

  const channel = getChannel(activeChannelId)

  function handleSelectChannel(id, postId) {
    setActiveChannelId(id)
    setOpenForumPostId(postId ?? null)
  }

  return (
    <div className="flex h-screen overflow-hidden bg-dc-chat font-sans">
      <ServerRail />
      <ChannelSidebar
        activeChannelId={activeChannelId}
        onSelectChannel={handleSelectChannel}
        resolvedCount={resolvedCount}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <ChannelHeader
          icon={channel.icon}
          title={channel.label}
          topic={channel.kind === 'placeholder' ? undefined : channel.topic}
          resolved={channel.kind === 'qa' && threadResolved}
          showMembers={showMembers}
          onToggleMembers={() => setShowMembers((v) => !v)}
        />

        <div className="flex min-h-0 flex-1">
          <div className="flex min-w-0 flex-1 flex-col">
            {channel.kind === 'qa' && (
              <HoiDapChannel
                onResolvedCountChange={setResolvedCount}
                onThreadResolvedChange={setThreadResolved}
              />
            )}
            {channel.kind === 'chat' && <GeneralChannel />}
            {channel.kind === 'forum' && (
              <ForumChannel openPostId={openForumPostId} onOpenPost={setOpenForumPostId} />
            )}
            {channel.kind === 'info' && <InfoChannel />}
            {channel.kind === 'placeholder' && <PlaceholderChannel label={channel.label} />}
          </div>

          {showMembers && <MemberList />}
        </div>
      </div>
    </div>
  )
}
