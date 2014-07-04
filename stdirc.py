from twisted.words.protocols import irc
from twisted.protocols import basic
from twisted.internet import reactor, protocol, stdio
import argparse


class StdinReader(basic.LineReceiver):
	from os import linesep as delimiter

	def __init__(self, factory):
		self.factory = factory

	def lineReceived(self, line):
		self.factory.client.msg(self.factory.channel, line)

	def connectionLost(self, reason):
		self.factory.quitting = True
		self.factory.client.quit('stdin closed')


class PipeBot(irc.IRCClient):
	def signedOn(self):
		# Join channel on signon
		self.join(self.factory.channel)

	def joined(self, channel):
		# Setup StandardIO on join channel.
		stdio.StandardIO(StdinReader(f))

	def alterCollidedNick(self, nickname):
		# Avoid nick collisions
		return nickname + '_'


class PipeBotFactory(protocol.ClientFactory):
	def __init__(self, channel, nick):
		self.channel = channel
		self.nick = nick
		self.quitting = False

	def buildProtocol(self, addr):
		p = PipeBot()
		p.factory = self
		p.nickname = self.nick or 'stdIRC'
		self.client = p
		return p

	def clientConnectionLost(self, connector, reason):
		if self.quitting:
			reactor.stop()
		else:
			connector.connect()  # Reconnect on disconnect.

	def clientConnectionFailed(self, connector, reason):
		print "IRC Connection Failed:", reason
		reactor.stop()


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("server", help="The IRC server to connect to.")
	parser.add_argument("port", help="The port on the IRC server to connect to.", type=int)
	parser.add_argument("channel", help="The channel to join on the IRC server.")
	parser.add_argument("nick", help="The nick to use on the IRC server.", nargs='?', default=None)
	args = parser.parse_args()

	f = PipeBotFactory(args.channel, args.nick)
	reactor.connectTCP(args.server, args.port, f)
	reactor.run()