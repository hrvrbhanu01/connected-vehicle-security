const { Contract } = require('fabric-contract-api');

class RecordEvent extends Contract {
    async InitLedger(ctx) {
        console.info('============= START : Initialize Ledger ===========');
        const events = [];
        await ctx.stub.putState('EVENTS', Buffer.from(JSON.stringify(events)));
        console.info('============= END : Initialize Ledger ===========');
    }

    async recordEvent(ctx, eventData) {
        console.info('============= START : Record Event ===========');
        
        const eventsBuffer = await ctx.stub.getState('EVENTS');
        const events = JSON.parse(eventsBuffer.toString());
        
        const event = {
            id: `event_${Date.now()}`,
            timestamp: new Date().toISOString(),
            data: eventData,
            hash: this._hashEvent(eventData)
        };
        
        events.push(event);
        await ctx.stub.putState('EVENTS', Buffer.from(JSON.stringify(events)));
        
        console.info('============= END : Record Event ===========');
        return JSON.stringify(event);
    }

    async verifyEvent(ctx, eventId) {
        const eventsBuffer = await ctx.stub.getState('EVENTS');
        const events = JSON.parse(eventsBuffer.toString());
        
        const event = events.find(e => e.id === eventId);
        if (!event) throw new Error('Event not found');
        
        const currentHash = this._hashEvent(event.data);
        if (currentHash !== event.hash) {
            throw new Error('Event data has been tampered with');
        }
        
        return JSON.stringify({ valid: true, event });
    }

    _hashEvent(data) {
        const crypto = require('crypto');
        return crypto.createHash('sha256').update(JSON.stringify(data)).digest('hex');
    }
}

module.exports = RecordEvent;