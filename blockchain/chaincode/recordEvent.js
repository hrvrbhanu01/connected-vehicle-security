const { Contract } = require('fabric-contract-api');
const crypto = require('crypto');

class RecordEvent extends Contract {
    async InitLedger(ctx) {
        console.info('============= START : Initialize Ledger ===========');
        const events = [];
        await ctx.stub.putState('EVENTS', Buffer.from(JSON.stringify(events)));
        console.info('============= END : Initialize Ledger ===========');
        return JSON.stringify({ message: 'Ledger initialized successfully', eventsCount: 0 });
    }

    async recordEvent(ctx, eventData) {
        console.info('============= START : Record Event ===========');
        
        try {
            // Parse eventData if it's a string
            let parsedEventData;
            if (typeof eventData === 'string') {
                try {
                    parsedEventData = JSON.parse(eventData);
                } catch (parseError) {
                    parsedEventData = eventData;
                }
            } else {
                parsedEventData = eventData;
            }

            // Get existing events or initialize empty array
            let events = [];
            const eventsBuffer = await ctx.stub.getState('EVENTS');
            
            if (eventsBuffer && eventsBuffer.length > 0) {
                try {
                    events = JSON.parse(eventsBuffer.toString());
                } catch (error) {
                    console.warn('Could not parse existing events, starting fresh');
                    events = [];
                }
            }
            
            // Use deterministic values that will be the same across all peers
            const txId = ctx.stub.getTxID();
            const timestamp = ctx.stub.getTxTimestamp();
            
            const event = {
                id: `event_${txId}`,
                timestamp: timestamp.seconds.toString(),
                timestampNanos: timestamp.nanos.toString(),
                data: parsedEventData,
                hash: this._hashEvent(parsedEventData),
                txId: txId,
                mspId: ctx.clientIdentity.getMSPID()
            };
            
            events.push(event);
            await ctx.stub.putState('EVENTS', Buffer.from(JSON.stringify(events)));
            
            console.info(`Event recorded with ID: ${event.id}`);
            console.info('============= END : Record Event ===========');
            
            return JSON.stringify({
                success: true,
                event: event,
                totalEvents: events.length
            });

        } catch (error) {
            console.error('Error in recordEvent:', error);
            const errorResponse = {
                success: false,
                error: error.message,
                timestamp: ctx.stub.getTxTimestamp().seconds.toString()
            };
            return JSON.stringify(errorResponse);
        }
    }

    async verifyEvent(ctx, eventId) {
        console.info('============= START : Verify Event ===========');
        
        try {
            const eventsBuffer = await ctx.stub.getState('EVENTS');
            
            if (!eventsBuffer || eventsBuffer.length === 0) {
                throw new Error('No events found in ledger');
            }

            const events = JSON.parse(eventsBuffer.toString());
            const event = events.find(e => e.id === eventId);
            
            if (!event) {
                throw new Error(`Event with ID ${eventId} not found`);
            }
            
            const currentHash = this._hashEvent(event.data);
            const isValid = currentHash === event.hash;
            
            console.info('============= END : Verify Event ===========');
            
            return JSON.stringify({
                valid: isValid, 
                event: event,
                currentHash: currentHash,
                originalHash: event.hash,
                timestamp: ctx.stub.getTxTimestamp().seconds.toString()
            });

        } catch (error) {
            console.error('Error in verifyEvent:', error);
            return JSON.stringify({
                valid: false,
                error: error.message,
                timestamp: ctx.stub.getTxTimestamp().seconds.toString()
            });
        }
    }

    async getAllEvents(ctx) {
        console.info('============= START : Get All Events ===========');
        
        try {
            const eventsBuffer = await ctx.stub.getState('EVENTS');
            
            if (!eventsBuffer || eventsBuffer.length === 0) {
                return JSON.stringify({ events: [], count: 0 });
            }

            const events = JSON.parse(eventsBuffer.toString());
            
            console.info('============= END : Get All Events ===========');
            
            return JSON.stringify({ 
                events: events, 
                count: events.length,
                timestamp: ctx.stub.getTxTimestamp().seconds.toString()
            });

        } catch (error) {
            console.error('Error in getAllEvents:', error);
            return JSON.stringify({
                events: [],
                count: 0,
                error: error.message,
                timestamp: ctx.stub.getTxTimestamp().seconds.toString()
            });
        }
    }

    _hashEvent(data) {
        return crypto.createHash('sha256').update(JSON.stringify(data)).digest('hex');
    }
}

module.exports = RecordEvent;